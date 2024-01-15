from django import forms
from rest_framework import generics, permissions, serializers
from rest_framework.authentication import BasicAuthentication
from knox.views import LoginView as KnoxLoginView

from api.models import ChargeSession, Wallbox, RFIDToken
from api.serializers import ChargeSessionSerializer, WallboxSerializer, RFIDSerializer


def validate(params, param_name, field_type, *args, **kwargs):
    field = field_type(*args, **kwargs)
    cleaned = field.clean(params.get(param_name))
    return cleaned


class LoginView(KnoxLoginView):
    authentication_classes = [BasicAuthentication]


class ChargeSessionList(generics.ListAPIView):
    """
    Retrieve a list of all charge sessions.
    """
    model = ChargeSession
    serializer_class = ChargeSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ChargeSession.objects.all().order_by('-sessionID')
        try:
            not_before = validate(self.request.query_params, 'not_before', forms.DateField, required=False)
            not_after = validate(self.request.query_params, 'not_after', forms.DateField, required=False)
            tokens = validate(self.request.query_params, 'tokens', forms.CharField, required=False)
        except forms.ValidationError as e:
            raise serializers.ValidationError(e.message)
        if not_before:
            queryset = queryset.filter(started__gte=not_before)
        if not_after:
            queryset = queryset.filter(ended__lte=not_after)
        if tokens:
            tokens = tokens.split(',')
            try:
                tokens = [int(token) for token in tokens]
            except ValueError:
                raise serializers.ValidationError('tokens must be an integer list')
            queryset = queryset.filter(token__in=tokens)
        return queryset


class WallboxList(generics.ListAPIView):
    """
    Retrieve the current status of all known wallboxes.
    """
    model = Wallbox
    serializer_class = WallboxSerializer
    queryset = Wallbox.objects.all()
    permission_classes = [permissions.IsAuthenticated]


class RFIDTokenList(generics.ListAPIView):
    """
    Retrieve the current list of all RFID tokens.
    """
    model = RFIDToken
    serializer_class = RFIDSerializer
    queryset = RFIDToken.objects.all()
    permission_classes = [permissions.IsAuthenticated]
