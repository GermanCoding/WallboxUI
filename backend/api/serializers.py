import datetime
from django.utils import timezone

from rest_framework import serializers

from api.models import ChargeSession, RFIDToken, Wallbox


class RFIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFIDToken
        exclude = []


class ChargeSessionSerializer(serializers.ModelSerializer):
    token = RFIDSerializer()

    class Meta:
        model = ChargeSession
        exclude = []


class WallboxSerializer(serializers.ModelSerializer):
    uptime = serializers.SerializerMethodField()

    class Meta:
        model = Wallbox
        exclude = []

    def get_uptime(self, obj):
        return int(obj.uptime.total_seconds()) + int((timezone.now() - obj.lastUpdated).total_seconds())
