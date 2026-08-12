from django.contrib.auth import authenticate as drf_authenticate
from django.contrib.auth import logout as drf_logout
from django.contrib.auth.models import auth
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets
from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
from api_app import server_helper
from .mcp_configuration import MCPConfigurationService, MCPTokenService
from .shared_functions import (
    get_connected_peers,
    get_iptables_log,
    get_license as read_license,
    get_wireguard_configuration,
    restart_wireguard,
)
from .email_service import (
    EmailConfigurationError, EmailDeliveryError, EmailRecipientError,
    email_peer_configuration, send_test_email as deliver_test_email,
)


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


class PeerEmailRequestSerializer(serializers.Serializer):
    peer_id = serializers.IntegerField(min_value=1)

    def to_internal_value(self, data):
        if not hasattr(data, "keys") or set(data.keys()) != {"peer_id"}:
            raise serializers.ValidationError({"detail": "Only peer_id is accepted."})
        return super().to_internal_value(data)


class TestEmailRequestSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not hasattr(data, "keys") or data:
            raise serializers.ValidationError({"detail": "No request fields are accepted."})
        return super().to_internal_value(data)


class ServerConfigurationViewSet(viewsets.ModelViewSet, UpdateModelMixin):
    queryset = ServerConfiguration.objects.all()
    serializer_class = ServerConfigurationSerializer
    permission_classes = (IsAuthenticated,)

    def perform_update(self, serializer):
        serializer.save()
        super().perform_update(serializer)
        cache.delete(CACHE_KEY_APP_LIVE_VERSION)


class MCPConfigurationView(APIView):
    """Session-authenticated MCP administration configuration endpoint."""
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        configuration = ServerConfiguration.objects.first()
        if configuration is None:
            return Response({"detail": "ServerConfiguration is not initialized."}, status=404)
        return Response(MCPConfigurationService.status(configuration))

    def patch(self, request):
        configuration = ServerConfiguration.objects.first()
        if configuration is None:
            return Response({"detail": "ServerConfiguration is not initialized."}, status=404)
        if "mcp_enabled" not in request.data or not isinstance(request.data["mcp_enabled"], bool):
            return Response({"mcp_enabled": ["A boolean value is required."]}, status=400)
        configuration.mcp_enabled = request.data["mcp_enabled"]
        if configuration.mcp_enabled and not configuration.mcp_token:
            MCPTokenService.rotate(configuration)
        configuration.save(update_fields=["mcp_enabled"])
        return Response(MCPConfigurationService.status(configuration))


class MCPTokenView(APIView):
    """Authenticated token rotation and raw-token retrieval for clipboard copy."""
    authentication_classes = (SessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        configuration = ServerConfiguration.objects.first()
        if configuration is None:
            return Response({"detail": "ServerConfiguration is not initialized."}, status=404)
        MCPTokenService.rotate(configuration)
        return Response({**MCPConfigurationService.status(configuration), "token_rotated": True})

    def get(self, request):
        configuration = ServerConfiguration.objects.first()
        if configuration is None:
            return Response({"detail": "ServerConfiguration is not initialized."}, status=404)
        if not configuration.mcp_token:
            return Response({"detail": "MCP token is not configured."}, status=404)
        response = Response({"mcp_token": configuration.mcp_token})
        response["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response["Pragma"] = "no-cache"
        response["Expires"] = "0"
        return response


@api_view(["GET"])
def test(request):
    return Response({"message": "Hello from test!"})


@api_view(["GET"])
def get_license(request):
    return Response(read_license())


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def wireguard_generate_configuration_files(request):
    res = server_helper.generate_configuration_files()
    return Response(res)


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def wireguard_restart(request):
    sc = ServerConfiguration.objects.all()[0]
    res = restart_wireguard(sc)
    return Response({"message": "Hello from wireguard_restart!", "output": res})


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def wireguard_get_configuration(request):
    res = get_wireguard_configuration()
    return Response(res)


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
def wireguard_get_connected_peers(request):
    sc = ServerConfiguration.objects.all()[0]
    res = get_connected_peers(sc)
    return Response(res)


@api_view(["GET"])
@authentication_classes([SessionAuthentication])
def wireguard_get_iptables_log(request):
    res = get_iptables_log()
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
    res = server_helper.get_server_status()
    res["application_details"] = get_application_details()
    return Response(res)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def send_peer_email(request):
    request_serializer = PeerEmailRequestSerializer(data=request.data)
    if not request_serializer.is_valid():
        return Response(request_serializer.errors, status=400)
    try:
        peer = Peer.objects.get(pk=request_serializer.validated_data["peer_id"])
        email_peer_configuration(peer)
        return Response({"message": "Email sent successfully!"})
    except Peer.DoesNotExist:
        return Response({"message": "Peer was not found."}, status=404)
    except EmailRecipientError as exc:
        return Response({"message": str(exc)}, status=400)
    except EmailConfigurationError as exc:
        return Response({"message": str(exc)}, status=503)
    except EmailDeliveryError as exc:
        return Response({"message": str(exc)}, status=502)
    except Exception:
        from logging import getLogger
        getLogger(APP_NAME).exception("Unexpected peer email failure")
        return Response({"message": "The email could not be delivered. Check the server logs for more details."}, status=500)


@api_view(["POST"])
@authentication_classes([SessionAuthentication])
@permission_classes([IsAuthenticated])
def send_test_email(request):
    request_serializer = TestEmailRequestSerializer(data=request.data)
    if not request_serializer.is_valid():
        return Response(request_serializer.errors, status=400)
    try:
        deliver_test_email()
        return Response({"message": "Test email sent successfully!"})
    except EmailConfigurationError as exc:
        return Response({"message": str(exc)}, status=503)
    except EmailDeliveryError as exc:
        return Response({"message": str(exc)}, status=502)
    except Exception:
        from logging import getLogger
        getLogger(APP_NAME).exception("Unexpected test email failure")
        return Response({"message": "The test email could not be delivered. Check the server logs for more details."}, status=500)
