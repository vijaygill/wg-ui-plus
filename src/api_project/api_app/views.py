from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from rest_framework import viewsets

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt

from .models import Peer, PeerGroup, Target, ServerConfiguration
from .serializers import TargetSerializer
from .serializers import PeerGroupSerializer
from .serializers import PeerSerializer
from .serializers import ServerConfigurationSerializer


class PeerViewSet(viewsets.ModelViewSet):
    queryset = Peer.objects.all()
    serializer_class = PeerSerializer
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

