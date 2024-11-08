import base64
from django.conf import settings
from django.contrib.auth import authenticate as drf_authenticate
from django.contrib.auth import logout as drf_logout
from django.contrib.auth.models import auth
from django.core.cache import cache
from django.core.mail import EmailMessage
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

from .common import APP_NAME, CACHE_KEY_APP_LIVE_VERSION

from .models import Peer, PeerGroup, ServerConfiguration, Target
from .serializers import (
    PeerGroupSerializer,
    PeerSerializer,
    PeerWithQrSerializer,
    ServerConfigurationSerializer,
    TargetHeirarchySerializer,
    TargetSerializer,
)

from .server_helper import get_application_details
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
def get_server_status(request):
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
    res["application_details"] = get_application_details()
    return Response(res)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def send_peer_email(request):
    try:
        tunnel_qr_file = "tunnel.png"
        tunnel_conf_file = "tunnel.conf"
        subject = "Tunnel configuration sent from wg-ui-plus"
        body = f"""
The attached files are sent from {APP_NAME}.
Keep them safe.

Notify the administrator if you think the files have been compromised.
You will get new files generated and sent to you.

Do not share these files with anyone.

Do not use the files on multiple devices.
Get separate set of files generated for each device.

How to use {tunnel_qr_file}:
    This file is useful for the devices which can scan QR code.
    Install WireGuard client on the desired device.
    While adding a new tunnel, if the client allows scanning QR code,
    just point the camera to the attached QR image.

How to use {tunnel_conf_file}:
    This is used on the devices where the optiuon of scanning QR code is not available.
    Install WireGuard client on the desired device.
    While adding a new tunnel, add the tunnel by importing the file '{tunnel_conf_file}'.

"""
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [request.data["email_address"]]
        email = EmailMessage(
            subject=subject, body=body, from_email=from_email, to=recipient_list
        )
        email.attach(tunnel_qr_file, base64.b64decode(request.data["qr"]), "image/png")
        email.attach(tunnel_conf_file, request.data["configuration"], "text/plain")
        email.send(fail_silently=False)
        return Response({"message": "Email sent successfully!"})
    except Exception:
        return Response({"message": "Sending Email failed."}, status=503)
