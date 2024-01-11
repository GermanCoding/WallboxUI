from rest_framework import generics, permissions
from rest_framework.authentication import BasicAuthentication
from knox.views import LoginView as KnoxLoginView

from api.models import ChargeSession
from api.serializers import ChargeSessionSerializer


class LoginView(KnoxLoginView):
    authentication_classes = [BasicAuthentication]


class ChargeSessionList(generics.ListAPIView):
    """
    Retrieve a list of all charge sessions.
    """
    model = ChargeSession
    serializer_class = ChargeSessionSerializer
    queryset = ChargeSession.objects.all().order_by('-sessionID')
    permission_classes = [permissions.IsAuthenticated]
