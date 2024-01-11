import asyncio
import datetime
import functools
import json
import os
import signal
import time
from decimal import Decimal

import asyncudp
from django.core.management import BaseCommand

from api.models import Wallbox, ChargeSession, RFIDToken

WALLBOX_IP = "192.168.12.39"
WALLBOX_PORT = 7090
DESTINATION = (WALLBOX_IP, WALLBOX_PORT)
LOCAL_IP = "0.0.0.0"
# Note: It is important that the local socket is bound to the wallbox port - the wallbox is unable to respond otherwise.
SOURCE = (LOCAL_IP, WALLBOX_PORT)

PROBE_INTERVAL = 3600
MIN_WAIT = 0.1
RESPONSE_TIMEOUT = 5

BUILDUP = b'i'
SYSTEM_STATUS = b'report 1'
CONFIGURATION_STATUS = b'report 2'
CHARGING_STATUS = b'report 3'

schedule_probe = True


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


def validate_any_status(message):
    return validate_system_status(message) or validate_config_status(message) or validate_charging_status(message)


def validate_history_report(report_id, message):
    return validate_json(message, report_id)


def parse_datetime(timestring_start, timestring_end):
    format = "%Y-%m-%d %H:%M:%S.%f"
    start = datetime.strptime(timestring_start, format)
    start = start.replace(tzinfo=datetime.timezone.utc)
    end = datetime.strptime(timestring_end, format)
    end = end.replace(tzinfo=datetime.timezone.utc)
    return start, end


def parse_weak_timestamps(start_seconds, end_seconds, current_seconds):
    # current_offset is the wallbox current time in seconds since boot. Assuming that
    # we've received the data packet just now, this offset is more or less exactly
    # the current time (+ network/processing delays). We can then use this anchor in time
    # to compute the start and end time
    now = datetime.datetime.now(tz=datetime.timezone.utc).replace(microsecond=0)
    start_offset = current_seconds - start_seconds
    end_offset = current_seconds - end_seconds
    start = now - datetime.timedelta(seconds=start_offset)
    end = now - datetime.timedelta(seconds=end_offset)
    return start, end


async def update_from_report(report):
    serial = report['Serial']
    wallbox = await Wallbox.get_instance(serial)
    if report['ID'] == str(1):
        wallbox.product = report['Product']
        wallbox.serial = report['Serial']
        wallbox.firmwareVersion = report['Firmware']
        wallbox.timeStatus = Wallbox.time_status_from_raw(int(report['timeQ']))
    if report['ID'] == str(2):
        wallbox.state = Wallbox.state_from_raw(int(report['State']))
        wallbox.plug = Wallbox.plug_from_raw(int(report['Plug']))
    if report['ID'] == str(3):
        wallbox.currentChargePower = Decimal(report['P']) / Decimal(1000)
        wallbox.currentPowerFactor = Decimal(report['PF']) / Decimal(10)
        wallbox.currentSession = Decimal(report['E pres']) / Decimal(10)
        wallbox.energyMeter = Decimal(report['E total']) / Decimal(10)
    await wallbox.asave()


async def add_charge_session(raw_data):
    session = ChargeSession(pk=int(raw_data['Session ID']))
    session.hardwareCurrentLimit = int(raw_data['Curr HW'])
    session.energyMeterAtStart = Decimal(raw_data['E start']) / Decimal(10)
    session.chargedEnergy = Decimal(raw_data['E pres']) / Decimal(10)
    timesource = ChargeSession.time_status_from_raw(raw_data['timeQ'])
    if timesource == ChargeSession.WALLBOX_TIME_NTP:
        started, ended = parse_datetime(raw_data['started'], raw_data['ended'])
    else:  # For any other time source, use local time
        started, ended = parse_weak_timestamps(int(raw_data['started[s]']), int(raw_data['ended[s]']),
                                               int(raw_data['Sec']))
        timesource = ChargeSession.SERVER_TIME
    session.timesource = timesource
    session.started = started
    session.ended = ended
    session.stopReason = ChargeSession.reason_from_raw(int(raw_data['reason']))
    session.wallboxSerial = await Wallbox.get_instance(raw_data['Serial'])
    session.token = await RFIDToken.get_instance(raw_data['RFID tag'], raw_data['RFID class'])

    await session.asave()


class WallboxCommunicator:
    def __init__(self, socket):
        self.sock = socket

    async def _send(self, message, response_validator):
        while True:
            # Ensure we limit sending speed
            await asyncio.sleep(MIN_WAIT)
            self.sock.sendto(message)
            try:
                data, addr = await asyncio.wait_for(self.sock.recvfrom(), timeout=RESPONSE_TIMEOUT)
            except TimeoutError:
                print(f"Did not receive a response in time, resending {message}")
                continue
            response = data.decode("utf-8")
            if addr != DESTINATION:
                print(f"Received packet from unauthorized address {addr}, ignoring")
                continue
            if not response_validator(response):
                global schedule_probe
                print(f"Response received did not pass validation, scheduling probe")
                print(f"Request was {message}, response was {response}")
                schedule_probe = True
                continue
            return response

    async def search_for_new_sessions(self):
        for history_entries in range(1, 31):
            history_id = 100 + history_entries
            report = ("report " + str(history_id)).encode("utf-8")
            entry = json.loads(await self._send(report, functools.partial(validate_history_report, history_id)))
            session_id = entry["Session ID"]
            if session_id == -1:
                # Empty entry. All subsequent ones will be empty too.
                break
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
        charging_status = json.loads(await self._send(CHARGING_STATUS, validate_charging_status))
        print(f"Charging status: {json.dumps(charging_status, indent=4)}")
        await update_from_report(system_status)
        await update_from_report(config_status)
        await update_from_report(charging_status)
        await self.search_for_new_sessions()
        return True

    async def receive_status(self):
        while True:
            try:
                data, addr = await asyncio.wait_for(self.sock.recvfrom(), timeout=PROBE_INTERVAL)
            except TimeoutError:
                return None
            response = data.decode("utf-8")
            if addr != DESTINATION:
                print(f"Received packet from unauthorized address {addr}, ignoring")
                continue
            if not validate_any_status(response):
                global schedule_probe
                print(
                    f"Expected to receive status message, but received message did not pass validation, scheduling probe")
                print(f"Response was {response}")
                return False
            report = json.loads(response)
            print(f"Received status message {report}")
            update_from_report(report)
            if report["ID"] == str(2):
                # Report 2 includes state changes, which may indicate that there are new sessions.
                await self.search_for_new_sessions()
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
        if schedule_probe or (time.time() - last_probe) >= PROBE_INTERVAL:
            if await comm.probe():
                last_probe = time.time()
                schedule_probe = False
        else:
            if not await comm.receive_status():
                schedule_probe = True


class Command(BaseCommand):
    help = "Talk to Wallbox, receive charge sessions, status reports and control messages"

    def handle(self, **options) -> str:
        asyncio.run(main())
