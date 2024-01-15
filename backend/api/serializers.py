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
    class Meta:
        model = Wallbox
        exclude = []
