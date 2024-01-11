from rest_framework import serializers

from api.models import ChargeSession, RFIDToken


class RFIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFIDToken
        fields = ['name', 'tokenID', 'tokenClass']


class ChargeSessionSerializer(serializers.ModelSerializer):
    token = RFIDSerializer()

    class Meta:
        model = ChargeSession
        fields = ['sessionID', 'hardwareCurrentLimit', 'energyMeterAtStart', 'chargedEnergy', 'started', 'ended',
                  'stopReason', 'token']
