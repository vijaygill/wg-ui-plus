import json
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from rest_framework import viewsets

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers
from django.contrib.auth import authenticate as drf_authenticate
from django.contrib.auth import logout as drf_logout
from django.contrib.auth.models import User, auth

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import authentication_classes, permission_classes

from .models import Peer, PeerGroup, Target, ServerConfiguration
from .serializers import TargetSerializer
from .serializers import PeerGroupSerializer
from .serializers import PeerSerializer, PeerWithQrSerializer
from .serializers import ServerConfigurationSerializer
from .serializers import TargetHeirarchySerializer

from .wireguardhelper import WireGuardHelper


class PeerViewSet(viewsets.ModelViewSet):
    queryset = Peer.objects.all()
    serializer_class = PeerSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == "retrieve" or self.action == "update":
            return PeerWithQrSerializer
        return super().get_serializer_class()


class TargetHeirarchyViewSet(viewsets.ModelViewSet):
    queryset = Target.objects.all()
    serializer_class = TargetHeirarchySerializer
    permission_classes = [AllowAny]


class PeerGroupViewSet(viewsets.ModelViewSet):
    queryset = PeerGroup.objects.all()
    serializer_class = PeerGroupSerializer
    permission_classes = [AllowAny]


class TargetViewSet(viewsets.ModelViewSet):
    queryset = Target.objects.all()
    serializer_class = TargetSerializer
    permission_classes = [AllowAny]


class ServerConfigurationViewSet(viewsets.ModelViewSet):
    queryset = ServerConfiguration.objects.all()
    serializer_class = ServerConfigurationSerializer
    permission_classes = [AllowAny]


@api_view(["GET"])
def test(request):
    return Response({"message": "Hello from test!"})


@api_view(["GET"])
def get_license(request):
    with open("/app/LICENSE") as f:
        text = f.read()
        return HttpResponse(json.dumps({"license": text}))


def wireguard_generate_configuration_files(request):
    wg = WireGuardHelper()
    sc = ServerConfiguration.objects.all()[0]
    peer_groups = PeerGroup.objects.all()
    peers = Peer.objects.all()
    targets = Target.objects.all()
    res = wg.generateConfigurationFiles(
        serverConfiguration=sc, targets=targets, peer_groups=peer_groups, peers=peers
    )
    return HttpResponse(json.dumps(res))


def wireguard_restart(request):
    wg = WireGuardHelper()
    sc = ServerConfiguration.objects.all()[0]
    res = wg.restart(serverConfiguration=sc)
    return HttpResponse(
        json.dumps({"message": "Hello from wireguard_restart!", "output": res})
    )


def wireguard_get_configuration(request):
    wg = WireGuardHelper()
    sc = ServerConfiguration.objects.all()[0]
    peers = Peer.objects.all()
    res = wg.getWireguardConfiguration(serverConfiguration=sc, peers=peers)
    res = json.dumps(res)
    return HttpResponse(res)


def wireguard_get_connected_peers(request):
    peers = Peer.objects.all()
    wg = WireGuardHelper()
    res = wg.get_connected_peers(peers)
    res = json.dumps(res)
    return HttpResponse(res)


def wireguard_get_iptables_log(request):
    wg = WireGuardHelper()
    res = wg.get_iptables_log()
    res = json.dumps(res)
    return HttpResponse(res)


@csrf_exempt
# @api_view(["GET", "POST"])
def login(request):
    res = {}
    if request.method == "GET":
        res = {
            "is_logged_in": request.user.is_authenticated,
            "message": "Already logged in." if request.user.is_authenticated else "Not logged in.",
        }
    if request.method == "POST":
        if request.user.is_authenticated:
            res = {"is_logged_in": True, "message": "Already logged in."}
        else:
            # cred = request.data #used with @api_view only but that causes session to be lost
            cred = json.loads(request.body)
            username = cred["username"].strip() if cred["username"] else ''
            password = cred["password"].strip() if cred["password"] else ''
            user = drf_authenticate(username=username, password=password)
            if user:
                auth.login(request, user)
                res = {"is_logged_in": True, "message": "Logged in now."}
            else:
                res = {"is_logged_in": False, "message": "Not logged in."}
    return HttpResponse(json.dumps(res))

def logout(request):
    drf_logout(request=request)
    res = {"is_logged_in": False, "message": "User logged out."}
    return HttpResponse(json.dumps(res))
