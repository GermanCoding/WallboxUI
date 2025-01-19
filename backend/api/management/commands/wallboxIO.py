import asyncio
import datetime
import functools
import json
import os
import signal
import time
from decimal import Decimal
from urllib.error import URLError
import urllib.request

import asyncudp
from django.core.management import BaseCommand

from api.models import Wallbox, ChargeSession, RFIDToken, WALLBOX_TIME_NTP, SERVER_TIME, SESSION_CABLE_UNPLUGGED, \
    SESSION_CARD_DEAUTH, TIME_UNKNOWN, SESSION_RUNNING, SESSION_STATUS_UNKNOWN
from backend.settings import WALLBOX_IP, HEALTHCHECK_URL

WALLBOX_PORT = 7090
DESTINATION = (WALLBOX_IP, WALLBOX_PORT)
LOCAL_IP = "0.0.0.0"
# Note: It is important that the local socket is bound to the wallbox port - the wallbox is unable to respond otherwise.
SOURCE = (LOCAL_IP, WALLBOX_PORT)

PROBE_INTERVAL = 3600
PROBE_INTERVAL_RUNNING = 60
MIN_WAIT = 0.1
RESPONSE_TIMEOUT = 5

BUILDUP = b'i'
SYSTEM_STATUS = b'report 1'
CONFIGURATION_STATUS = b'report 2'
CHARGING_STATUS = b'report 3'
CURRENT_SESSION_STATUS = b'report 100'

schedule_probe = True
last_state = None


def validate_json(string, message_id=None):
    try:
        parsed = json.loads(string)
        if message_id is not None:
            return parsed['ID'] == str(message_id)
    except (ValueError, KeyError, TypeError, IndexError):
        return False


def validate_anything(message):
    return True


def validate_system_status(message):
    return validate_json(message, 1)


def validate_config_status(message):
    return validate_json(message, 2)


def validate_charging_status(message):
    return validate_json(message, 3)


def validate_current_charge_session(message):
    return validate_json(message, 100)


def validate_progress_report(message):
    try:
        parsed = json.loads(message)
        keys = parsed.keys()
        if len(keys) != 1:
            return False
        if next(iter(keys)) in ["E pres", "Max curr", "Enable sys", "Input", "Plug", "State"]:
            return True
    except (ValueError, KeyError, TypeError, IndexError):
        return False


def validate_history_report(report_id, message):
    return validate_json(message, report_id)


def parse_datetime(timestring_start, timestring_end):
    format = "%Y-%m-%d %H:%M:%S.%f"
    start = datetime.datetime.strptime(timestring_start, format)
    start = start.replace(tzinfo=datetime.timezone.utc)
    # End time may not be set for live sessions
    if timestring_end != "0":
        end = datetime.datetime.strptime(timestring_end, format)
        end = end.replace(tzinfo=datetime.timezone.utc)
    else:
        end = None
    return start, end


def parse_weak_timestamps(start_seconds, end_seconds, current_seconds):
    # Note: There is an undocumented feature here: "Sometimes", the wallbox puts a Unix timestamp
    # into these fields, instead of a relative time. We can detect this by looking for impossible values.
    if start_seconds > (current_seconds + 1):
        # Impossibly large start_seconds - probably unix time
        start = datetime.datetime.fromtimestamp(start_seconds, tz=datetime.timezone.utc)
        # Live session
        if end_seconds == 0:
            end = None
        else:
            end = datetime.datetime.fromtimestamp(end_seconds, tz=datetime.timezone.utc)
    else:
        # current_offset is the wallbox current time in seconds since boot. Assuming that
        # we've received the data packet just now, this offset is more or less exactly
        # the current time (+ network/processing delays). We can then use this anchor in time
        # to compute the start and end time
        now = datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0)
        start_offset = current_seconds - start_seconds
        end_offset = current_seconds - end_seconds
        start = now - datetime.timedelta(seconds=start_offset)
        end = now - datetime.timedelta(seconds=end_offset)
        # Live session
        if start_seconds > end_seconds == 0:
            end = None
    return start, end


async def parse_charge_session(raw_data):
    if int(raw_data['Session ID']) < 1:
        return None
    session = ChargeSession(pk=int(raw_data['Session ID']))
    session.hardwareCurrentLimit = int(raw_data['Curr HW'])
    session.energyMeterAtStart = Decimal(raw_data['E start']) / Decimal(10)
    session.chargedEnergy = Decimal(raw_data['E pres']) / Decimal(10)
    timesource = ChargeSession.time_status_from_raw(raw_data['timeQ'])
    if timesource == WALLBOX_TIME_NTP:
        started, ended = parse_datetime(raw_data['started'], raw_data['ended'])
    else:  # For any other time source, use local time
        started, ended = parse_weak_timestamps(int(raw_data['started[s]']), int(raw_data['ended[s]']),
                                               int(raw_data['Sec']))
        timesource = SERVER_TIME
    session.timesource = timesource
    session.started = started
    session.ended = ended
    session.stopReason = ChargeSession.reason_from_raw(int(raw_data['reason']))
    session.wallboxSerial = await Wallbox.get_instance(raw_data['Serial'])
    session.token = await RFIDToken.get_instance(raw_data['RFID tag'], raw_data['RFID class'])
    return session


async def add_charge_session(raw_data):
    session = await parse_charge_session(raw_data)
    await session.asave()


async def update_from_report(report):
    serial = report['Serial']
    wallbox = await Wallbox.get_instance(serial)
    if report['ID'] == str(1):
        wallbox.product = report['Product']
        wallbox.serial = report['Serial']
        wallbox.firmwareVersion = report['Firmware']
        wallbox.timeStatus = Wallbox.time_status_from_raw(int(report['timeQ']))
        wallbox.uptime = datetime.timedelta(seconds=report['Sec'])
    if report['ID'] == str(2):
        wallbox.state = Wallbox.state_from_raw(int(report['State']))
        wallbox.plug = Wallbox.plug_from_raw(int(report['Plug']))
        wallbox.uptime = datetime.timedelta(seconds=report['Sec'])
    if report['ID'] == str(3):
        wallbox.currentChargePower = Decimal(report['P']) / Decimal(1000)
        wallbox.currentPowerFactor = Decimal(report['PF']) / Decimal(10)
        wallbox.currentSession = Decimal(report['E pres']) / Decimal(10)
        wallbox.energyMeter = Decimal(report['E total']) / Decimal(10)
        wallbox.phase1_voltage = Decimal(report['U1'])
        wallbox.phase2_voltage = Decimal(report['U2'])
        wallbox.phase3_voltage = Decimal(report['U3'])
        wallbox.phase1_current = Decimal(report['I1']) / Decimal(1000)
        wallbox.phase2_current = Decimal(report['I2']) / Decimal(1000)
        wallbox.phase3_current = Decimal(report['I3']) / Decimal(1000)
        wallbox.uptime = datetime.timedelta(seconds=report['Sec'])
    if report['ID'] == str(100):
        session = await parse_charge_session(report)
        if session is not None:
            wallbox.currentHardwareLimit = session.hardwareCurrentLimit
            wallbox.currentEnergyMeterAtStart = session.energyMeterAtStart
            wallbox.currentSession = session.chargedEnergy
            wallbox.currentStartTime = session.started
            # This is probably unnecessary since the parser will have already done this
            if report["ended[s]"] > 0:
                wallbox.currentEndTime = session.ended
            else:
                wallbox.currentEndTime = None
            if session.stopReason == SESSION_RUNNING and wallbox.currentEndTime is not None:
                # Sometimes, the wallbox reports that the session has ended, but the stopReason is put to 0 for some reason
                wallbox.currentSessionStatus = SESSION_STATUS_UNKNOWN
            wallbox.currentSessionStatus = session.stopReason
            wallbox.currentToken = session.token
            wallbox.currentSessionID = session.sessionID

    await wallbox.asave()


class WallboxCommunicator:
    def __init__(self, socket):
        self.last_state = None
        self.sock = socket

    async def _send(self, message, response_validator):
        resend = True
        while True:
            if resend:
                # Ensure we limit sending speed
                await asyncio.sleep(MIN_WAIT)
                self.sock.sendto(message)
                resend = False
            try:
                data, addr = await asyncio.wait_for(self.sock.recvfrom(), timeout=RESPONSE_TIMEOUT)
            except TimeoutError:
                print(f"Did not receive a response in time, resending {message}")
                resend = True
                continue
            response = data.decode("utf-8")
            if addr != DESTINATION:
                print(f"Received packet from unauthorized address {addr}, ignoring")
                continue
            if not response_validator(response):
                print(f"Response received did not pass validation, ignoring")
                print(f"Request was {message}, response was {response}")
                continue
            return response

    async def search_for_new_sessions(self):
        # report 100 is always the currently running session, 101 is sometimes the running session (but not always)
        for history_entries in range(1, 31):
            history_id = 100 + history_entries
            report = ("report " + str(history_id)).encode("utf-8")
            entry = json.loads(await self._send(report, functools.partial(validate_history_report, history_id)))
            session_id = entry["Session ID"]
            if session_id == -1:
                # Empty entry. All subsequent ones will be empty too.
                break
            if entry["reason"] not in [1, 10] and int(entry["ended[s]"]) == 0:
                # Charging session is still running (note that this has been observed to use undocumented reason IDs)
                # Skip it for now
                print(f"Debug: Skipping currently running session {session_id}")
                continue
            if await ChargeSession.try_find_session(session_id):
                # We already know this session, so we also know all subsequent ones.
                break
            print("New session!")
            print(f"{json.dumps(entry, indent=4)}")
            # This is a new session, save it
            await add_charge_session(entry)

    async def probe(self):
        await self._send(BUILDUP, validate_anything)
        system_status = json.loads(await self._send(SYSTEM_STATUS, validate_system_status))
        print(f"System status: {json.dumps(system_status, indent=4)}")
        config_status = json.loads(await self._send(CONFIGURATION_STATUS, validate_config_status))
        print(f"Config status: {json.dumps(config_status, indent=4)}")
        self.last_state = int(config_status['State'])
        charging_status = json.loads(await self._send(CHARGING_STATUS, validate_charging_status))
        print(f"Charging status: {json.dumps(charging_status, indent=4)}")
        current_session = json.loads(await self._send(CURRENT_SESSION_STATUS, validate_current_charge_session))
        print(f"Current session: {json.dumps(current_session, indent=4)}")
        await update_from_report(system_status)
        await update_from_report(config_status)
        await update_from_report(charging_status)
        await update_from_report(current_session)
        await self.search_for_new_sessions()
        return True

    async def receive_status(self):
        interval = PROBE_INTERVAL_RUNNING if self.last_state == 3 else PROBE_INTERVAL
        while True:
            try:
                data, addr = await asyncio.wait_for(self.sock.recvfrom(), timeout=interval)
            except TimeoutError:
                return None
            response = data.decode("utf-8")
            if addr != DESTINATION:
                print(f"Received packet from unauthorized address {addr}, ignoring")
                continue
            if not validate_progress_report(response):
                global schedule_probe
                print(
                    f"Expected to receive progress report message, but received message did not pass validation, scheduling probe")
                print(f"Response was {response}")
                return False
            report = json.loads(response)
            print(f"Received status message {report}")
            if not report.get("E pres", None):
                print("Some state changed (except energy meter), scheduling probe")
                return False
            return True

    def __del__(self):
        self.sock.close()


def stop(loop):
    loop.stop()


async def main():
    global schedule_probe
    loop = asyncio.get_running_loop()
    if os.name == 'posix':
        for signame in {'SIGINT', 'SIGTERM'}:
            loop.add_signal_handler(getattr(signal, signame), functools.partial(stop, loop))
        print(f"Starting endless loop; Send CTRL+C (SIGINT or SIGTERM) to exit.")
    else:
        print(f"Starting endless loop")
    schedule_probe = True
    sock = await asyncudp.create_socket(local_addr=SOURCE, remote_addr=DESTINATION)
    comm = WallboxCommunicator(sock)
    last_probe = time.time()
    while True:
        interval = PROBE_INTERVAL_RUNNING if comm.last_state == 3 else PROBE_INTERVAL
        print(f"Debug: using interval {interval}, state {comm.last_state}")
        if schedule_probe or (time.time() - last_probe) >= interval:
            if await comm.probe():
                last_probe = time.time()
                schedule_probe = False
                try:
                    loop = asyncio.get_event_loop()
                    future = loop.run_in_executor(None, urllib.request.urlopen, HEALTHCHECK_URL)
                    await future
                except URLError:
                    print("Unable to notify probe success to health checks")
        else:
            if not await comm.receive_status():
                schedule_probe = True


class Command(BaseCommand):
    help = "Talk to Wallbox, receive charge sessions, status reports and control messages"

    def handle(self, **options) -> str:
        asyncio.run(main())
        return "Exit."
