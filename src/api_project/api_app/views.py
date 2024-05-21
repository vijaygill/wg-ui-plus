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
        if self.action == 'retrieve':
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

def test(request):
    return HttpResponse(json.dumps({'message': 'Hello from test!'}))

def wireguard_generate_configuration_files(request):
    wg = WireGuardHelper()
    sc = ServerConfiguration.objects.all()[0]
    peers = Peer.objects.all()
    targets = Target.objects.all()
    res = wg.generateConfigurationFiles(serverConfiguration=sc, targets=targets, peers=peers)
    return HttpResponse(json.dumps(res))

def wireguard_restart(request):
    wg = WireGuardHelper()
    sc = ServerConfiguration.objects.all()[0]
    res = wg.restart(serverConfiguration=sc)
    return HttpResponse(json.dumps({'message': 'Hello from wireguard_restart!', 'output': res }))

def wireguard_get_configuration(request):
    wg = WireGuardHelper()
    sc = ServerConfiguration.objects.all()[0]
    peers = Peer.objects.all()
    res = wg.getWireguardConfiguration(serverConfiguration=sc, peers= peers)
    res = json.dumps(res)
    return HttpResponse(res)
