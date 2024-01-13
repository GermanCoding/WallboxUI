from decimal import Decimal

from django.contrib import admin
from django.db import models
from django.conf import settings


# An RFID card used for authorization on the wallbox.
class RFIDToken(models.Model):
    class Meta:
        verbose_name_plural = "RFID Tokens"

    tokenID = models.CharField(max_length=20)
    tokenClass = models.CharField(max_length=20)
    name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        if self.name:
            return str(self.name)
        else:
            return str(self.tokenID) + "/" + str(self.tokenClass)

    @classmethod
    async def get_instance(cls, tag, t_class):
        (obj, created) = await cls.objects.aget_or_create(tokenID=tag, tokenClass=t_class)
        return obj


class Wallbox(models.Model):
    class Meta:
        verbose_name_plural = "Wallboxes"
        db_table_comment = "Test Comment"

    UC_TQ_NONE = "UC_TQ_NONE"
    UC_TQ_NOT_SYNCED = "UC_TQ_NOT_SYNCED"
    UC_TQ_WEAK = "UC_TQ_WEAK"
    UC_TQ_STRONG = "UC_TQ_STRONG"
    UC_TQ_UNKNOWN = "UC_TQ_UNKNOWN"
    TIME_STATUS = {
        UC_TQ_NONE: "No time quality. Clock was never set.",
        UC_TQ_NOT_SYNCED: "Clock was set but not really synchronized e.g. build time was used.",
        UC_TQ_WEAK: "Clock was synchronized using an unreliable source.",
        UC_TQ_STRONG: "Clock was synchronized using a reliable source (NTP, OCPP, etc.).",
        UC_TQ_UNKNOWN: "Time quality is unknown."
    }
    STATE_STARTUP = "STATE_STARTUP"
    STATE_NOT_READY = "STATE_NOT_READY"
    STATE_READY = "STATE_READY"
    STATE_CHARGING = "STATE_CHARGING"
    STATE_ERROR = "STATE_ERROR"
    STATE_INTERRUPTED = "STATE_INTERRUPTED"
    STATE_UNKNOWN = "STATE_UNKNOWN"
    STATES = {
        STATE_STARTUP: "Startup",
        STATE_NOT_READY: "Not ready for charging, authorization locked or not connected to vehicle",
        STATE_READY: "Ready for charging and waiting for reaction from vehicle",
        STATE_CHARGING: "Charging",
        STATE_ERROR: "Error is present",
        STATE_INTERRUPTED: "Temporarily interrupted",
        STATE_UNKNOWN: "Unknown",
    }
    PLUG_CABLE_UNPLUGGED = "PLUG_CABLE_UNPLUGGED"
    PLUG_CABLE_UNLOCKED_NOT_CONNECTED = "PLUG_CABLE_UNLOCKED_NOT_CONNECTED"
    PLUG_CABLE_LOCKED_NOT_CONNECTED = "PLUG_CABLE_LOCKED_NOT_CONNECTED"
    PLUG_CABLE_CONNECTED_UNLOCKED = "PLUG_CABLE_CONNECTED_UNLOCKED"
    PLUG_CABLE_CONNECTED_LOCKED = "PLUG_CABLE_CONNECTED_LOCKED"
    PLUG_CABLE_UNKNOWN = "PLUG_CABLE_UNKNOWN"
    PLUG_STATES = {
        PLUG_CABLE_UNPLUGGED: "No cable is plugged.",
        PLUG_CABLE_UNLOCKED_NOT_CONNECTED: "Cable is plugged into charging station, but not connected or locked.",
        PLUG_CABLE_LOCKED_NOT_CONNECTED: "Cable is plugged into charging station and locked, but not connected to vehicle.",
        PLUG_CABLE_CONNECTED_UNLOCKED: "Cable is plugged into charging station and vehicle but not locked.",
        PLUG_CABLE_CONNECTED_LOCKED: "Cable is plugged into charging station and vehicle, furthermore the cable is locked.",
        PLUG_CABLE_UNKNOWN: "Cable status is unknown.",
    }
    serial = models.CharField(max_length=255, primary_key=True)
    product = models.CharField(max_length=255, default="unknown")
    firmwareVersion = models.CharField(max_length=255, default="unknown")
    timeStatus = models.CharField(max_length=255, choices=TIME_STATUS, default=UC_TQ_UNKNOWN)
    state = models.CharField(max_length=255, choices=STATES, default=STATE_UNKNOWN)
    plug = models.CharField(max_length=255, choices=PLUG_STATES, default=PLUG_CABLE_UNKNOWN)
    currentChargePower = models.DecimalField(max_digits=9, decimal_places=3, default=Decimal(0))
    currentPowerFactor = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal(0))
    currentSession = models.DecimalField(max_digits=9, decimal_places=1, default=Decimal(0))
    energyMeter = models.DecimalField(max_digits=9, decimal_places=1, default=Decimal(0))
    lastUpdated = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.product:
            return f"{str(self.product)} ({self.serial})"
        else:
            return f"{self.serial}"

    @classmethod
    async def get_instance(cls, serial):
        (obj, created) = await cls.objects.aget_or_create(serial=serial)
        return obj

    @classmethod
    def time_status_from_raw(cls, raw_id):
        id_map = {
            0: cls.UC_TQ_NONE,
            1: cls.UC_TQ_NOT_SYNCED,
            2: cls.UC_TQ_WEAK,
            3: cls.UC_TQ_STRONG
        }
        try:
            return id_map[raw_id]
        except KeyError:
            return cls.UC_TQ_UNKNOWN

    @classmethod
    def state_from_raw(cls, raw_id):
        id_map = {
            0: cls.STATE_STARTUP,
            1: cls.STATE_NOT_READY,
            2: cls.STATE_READY,
            3: cls.STATE_CHARGING,
            4: cls.STATE_ERROR,
            5: cls.STATE_INTERRUPTED
        }
        try:
            return id_map[raw_id]
        except KeyError:
            return cls.STATE_UNKNOWN

    @classmethod
    def plug_from_raw(cls, raw_id):
        id_map = {
            0: cls.PLUG_CABLE_UNPLUGGED,
            1: cls.PLUG_CABLE_UNLOCKED_NOT_CONNECTED,
            3: cls.PLUG_CABLE_LOCKED_NOT_CONNECTED,
            5: cls.PLUG_CABLE_CONNECTED_UNLOCKED,
            7: cls.PLUG_CABLE_CONNECTED_LOCKED,
        }
        try:
            return id_map[raw_id]
        except KeyError:
            return cls.PLUG_CABLE_UNKNOWN


# A charge session recorded by the wallbox.
class ChargeSession(models.Model):
    class Meta:
        ordering = ('sessionID',)

    WALLBOX_TIME_NTP = "WALLBOX_TIME_NTP"
    WALLBOX_TIME_WEAK = "WALLBOX_TIME_WEAK"
    SERVER_TIME = "SERVER_TIME"
    TIME_UNKNOWN = "TIME_UNKNOWN"
    TIMESOURCES = {
        WALLBOX_TIME_NTP: "Wallbox self-synchronized NTP time",
        WALLBOX_TIME_WEAK: "Wallbox weak synced time",
        SERVER_TIME: "Server time based on Wallbox timer offset",
        TIME_UNKNOWN: "Unknown time source",
    }
    SESSION_RUNNING = "SESSION_RUNNING"
    SESSION_CABLE_UNPLUGGED = "SESSION_CABLE_UNPLUGGED"
    SESSION_CARD_DEAUTH = "SESSION_CARD_DEAUTH"
    SESSION_STATUS_UNKNOWN = "SESSION_STATUS_UNKNOWN"
    STOP_REASONS = {
        SESSION_RUNNING: "Charging session has not ended.",
        SESSION_CABLE_UNPLUGGED: "Charging session was terminated by unplugging.",
        SESSION_CARD_DEAUTH: "Charging session was terminated via deauthorization with the RFID card used for starting the session.",
        SESSION_STATUS_UNKNOWN: "The session's status is unknown.",
    }
    created = models.DateTimeField(auto_now_add=True)
    sessionID = models.IntegerField(primary_key=True)
    hardwareCurrentLimit = models.IntegerField()
    energyMeterAtStart = models.DecimalField(max_digits=9, decimal_places=1)
    chargedEnergy = models.DecimalField(max_digits=9, decimal_places=1)
    started = models.DateTimeField()
    ended = models.DateTimeField()
    timesource = models.CharField(max_length=255, choices=TIMESOURCES, default=TIME_UNKNOWN)
    stopReason = models.CharField(max_length=255, choices=STOP_REASONS, default=SESSION_STATUS_UNKNOWN)
    token = models.ForeignKey(RFIDToken, on_delete=models.PROTECT)
    wallboxSerial = models.ForeignKey(Wallbox, on_delete=models.PROTECT)

    def __str__(self):
        return str(self.sessionID)

    @classmethod
    async def try_find_session(cls, session_id):
        try:
            return await cls.objects.aget(sessionID=session_id)
        except cls.DoesNotExist:
            return None

    @classmethod
    def time_status_from_raw(cls, raw_id):
        raw_id = str(raw_id)
        if raw_id == "0":
            return cls.TIME_UNKNOWN
        if raw_id == "2":
            return cls.WALLBOX_TIME_WEAK
        if raw_id == "3" or raw_id == "X":
            return cls.WALLBOX_TIME_NTP
        return cls.TIME_UNKNOWN

    @classmethod
    def reason_from_raw(cls, raw_id):
        id_map = {
            0: cls.SESSION_RUNNING,
            1: cls.SESSION_CABLE_UNPLUGGED,
            10: cls.SESSION_CARD_DEAUTH,
        }
        try:
            return id_map[raw_id]
        except KeyError:
            return cls.SESSION_STATUS_UNKNOWN


# Don't show sensitive tables in the admin UI. This makes it harder to perform accidental modifications.
# (But do show it for development purposes)
if settings.DEBUG:
    admin.site.register(ChargeSession)
admin.site.register(RFIDToken)
admin.site.register(Wallbox)
