from rest_framework import serializers

from api.models import ChargeSession, RFIDToken, Wallbox


class RFIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = RFIDToken
        exclude = ['id']
        # fields = ['name', 'tokenID', 'tokenClass']


class ChargeSessionSerializer(serializers.ModelSerializer):
    token = RFIDSerializer()

    class Meta:
        model = ChargeSession
        exclude = ['created']
        # fields = ['sessionID', 'hardwareCurrentLimit', 'energyMeterAtStart', 'chargedEnergy', 'started', 'ended',
        #          'stopReason', 'token']


class WallboxSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallbox
        exclude = []
