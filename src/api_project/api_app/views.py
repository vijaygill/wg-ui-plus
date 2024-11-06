import os
import datetime
import requests
from django.contrib.auth import authenticate as drf_authenticate
from django.contrib.auth import logout as drf_logout
from django.contrib.auth.models import auth
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .common import logger
from .models import Peer, PeerGroup, ServerConfiguration, Target
from .serializers import (
    PeerGroupSerializer,
    PeerSerializer,
    PeerWithQrSerializer,
    ServerConfigurationSerializer,
    TargetHeirarchySerializer,
    TargetSerializer,
)
from .wireguardhelper import WireGuardHelper


class PeerViewSet(viewsets.ModelViewSet):
    queryset = Peer.objects.all()
    serializer_class = PeerSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if (
            self.action == "retrieve"
            or self.action == "update"
            or self.action == "create"
        ):
            return PeerWithQrSerializer
        return super().get_serializer_class()


class TargetHeirarchyViewSet(viewsets.ModelViewSet):
    queryset = Target.objects.all()
    serializer_class = TargetHeirarchySerializer


class PeerGroupViewSet(viewsets.ModelViewSet):
    queryset = PeerGroup.objects.all()
    serializer_class = PeerGroupSerializer
    permission_classes = (IsAuthenticated,)


class TargetViewSet(viewsets.ModelViewSet):
    queryset = Target.objects.all()
    serializer_class = TargetSerializer
    permission_classes = (IsAuthenticated,)


CACHE_KEY_APP_LIVE_VERSION = "CACHE_KEY_APP_LIVE_VERSION"


class ServerConfigurationViewSet(viewsets.ModelViewSet, UpdateModelMixin):
    queryset = ServerConfiguration.objects.all()
    serializer_class = ServerConfigurationSerializer
    permission_classes = (IsAuthenticated,)

    def perform_update(self, serializer):
        serializer.save()
        super().perform_update(serializer)
        cache.delete(CACHE_KEY_APP_LIVE_VERSION)


@api_view(["GET"])
def test(request):
    return Response({"message": "Hello from test!"})


@api_view(["GET"])
def get_license(request):
    with open("/app/LICENSE") as f:
        text = f.read()
        return Response({"license": text})


@api_view(["GET"])
def get_application_details(request):
    owner = "vijaygill"
    repo = "wg-ui-plus"
    latest_live_version = "unknown"
    current_version = "v0.0.0"
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    allow_check_updates = False
    try:
        current_version = os.environ.get("APP_VERSION", "v0.0.0")
    except Exception:
        current_version = "**Error**"
        pass
    try:
        sc = ServerConfiguration.objects.all()[0]
        allow_check_updates = sc.allow_check_updates
        latest_live_version = (
            "v0.0.0" if allow_check_updates else "Updates check diabled."
        )

        latest_live_version_temp = cache.get(CACHE_KEY_APP_LIVE_VERSION)
        if latest_live_version_temp:
            latest_live_version = latest_live_version_temp
        else:
            if allow_check_updates:
                response = requests.get(
                    f"https://github.com/{owner}/{repo}/releases/latest"
                )
                latest_live_version = response.url.split("/").pop()
                cache.add(CACHE_KEY_APP_LIVE_VERSION, latest_live_version, 60 * 60)
    except Exception:
        latest_live_version = "**Error**"
        pass

    return Response(
        {
            "current_time": current_time,
            "latest_live_version": latest_live_version,
            "current_version": current_version,
            "allow_allow_check_updates": allow_check_updates,
        }
    )


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def wireguard_generate_configuration_files(request):
    wg = WireGuardHelper()
    sc = ServerConfiguration.objects.all()[0]
    peer_groups = PeerGroup.objects.all()
    peers = Peer.objects.all()
    targets = Target.objects.all()
    res = wg.generate_configuration_files(
        serverConfiguration=sc, targets=targets, peer_groups=peer_groups, peers=peers
    )
    return Response(res)


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def wireguard_restart(request):
    wg = WireGuardHelper()
    sc = ServerConfiguration.objects.all()[0]
    res = wg.restart(serverConfiguration=sc)
    return Response({"message": "Hello from wireguard_restart!", "output": res})


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def wireguard_get_configuration(request):
    wg = WireGuardHelper()
    sc = ServerConfiguration.objects.all()[0]
    peers = Peer.objects.all()
    res = wg.get_wireguard_configuration(serverConfiguration=sc, peers=peers)
    return Response(res)


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
def wireguard_get_connected_peers(request):
    peers = Peer.objects.all()
    sc = ServerConfiguration.objects.all()[0]
    wg = WireGuardHelper()
    res = wg.get_connected_peers(peers, sc)
    return Response(res)


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
def wireguard_get_iptables_log(request):
    wg = WireGuardHelper()
    res = wg.get_iptables_log()
    return Response(res)


@csrf_exempt
@api_view(["GET", "POST"])
@authentication_classes([SessionAuthentication])
def auth_login(request):
    res = {}
    if request.method == "GET":
        res = {
            "is_logged_in": request.user.is_authenticated,
            "message": (
                "Already logged in."
                if request.user.is_authenticated
                else "Not logged in."
            ),
        }
    if request.method == "POST":
        if request.user.is_authenticated:
            res = {"is_logged_in": True, "message": "Already logged in."}
        else:
            cred = request.data
            username = cred["username"].strip() if cred["username"] else ""
            password = cred["password"].strip() if cred["password"] else ""
            user = drf_authenticate(username=username, password=password)
            if user:
                auth.login(request, user)
                res = {"is_logged_in": True, "message": "Logged in now."}
            else:
                res = {
                    "is_logged_in": False,
                    "message": "Login failed. Check username/password.",
                }
    return Response(res)


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
def auth_logout(request):
    drf_logout(request=request)
    res = {"is_logged_in": False, "message": "User logged out."}
    return Response(res)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def auth_change_password(request):
    user = request.user
    res = {"is_logged_in": user.is_authenticated, "message": ""}
    if user.is_authenticated:
        # cred = json.loads(request.body)
        cred = request.data
        current_password = (
            cred["current_password"].strip()
            if "current_password" in cred.keys()
            else ""
        )
        new_password = (
            cred["new_password"].strip() if "new_password" in cred.keys() else ""
        )
        new_password_copy = (
            cred["new_password_copy"].strip()
            if "new_password_copy" in cred.keys()
            else ""
        )
        if new_password != new_password_copy:
            res = {
                "is_logged_in": user.is_authenticated,
                "message": "New passwords don't match.",
            }
        else:
            if new_password:
                user = drf_authenticate(
                    username=user.username, password=current_password
                )
                if user:
                    auth.login(request, user)
                    user.set_password(new_password)
                    user.save()
                    res = {
                        "is_logged_in": user.is_authenticated,
                        "message": "Password changed.",
                    }
                else:
                    res = {
                        "is_logged_in": False,
                        "message": "Current password invalid.",
                    }
    return Response(res)


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
def wireguard_get_server_status(request):
    peers = Peer.objects.all()
    peer_groups = PeerGroup.objects.all()
    targets = Target.objects.all()
    server_configurations = ServerConfiguration.objects.all()
    last_changed_datetimes = (
        [x.last_changed_datetime for x in peers]
        + [x.last_changed_datetime for x in peer_groups]
        + [x.last_changed_datetime for x in targets]
        + [x.last_changed_datetime for x in server_configurations]
    )
    last_changed_datetime = (
        max(last_changed_datetimes) if last_changed_datetimes else None
    )
    wg = WireGuardHelper()
    res = wg.get_server_status(last_db_change_datetime=last_changed_datetime)
    return Response(res)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def send_peer_email(request):
    logger.warning(f'{request.data["id"]} - {request.data["email_address"]}')
    logger.warning(f'{request.data["configuration"]}')
    logger.warning(f'{request.data["qr"]}')
    return Response('Hola!')
