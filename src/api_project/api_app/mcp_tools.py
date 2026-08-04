"""Explicit, authenticated MCP tools for the WireGuard administration surface."""

import base64

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import EmailMessage
from rest_framework import serializers

from mcp_server import MCPToolset

from .common import APP_NAME, IS_EMAIL_ENABLED
from .models import Peer, PeerGroup, ServerConfiguration, Target
from .serializers import (
    PeerGroupSerializer,
    PeerWithQrSerializer,
    ServerConfigurationSerializer,
    TargetHeirarchySerializer,
    TargetSerializer,
)
from .server_helper import generate_configuration_files, get_application_details, get_server_status
from .wireguardhelper import WireGuardHelper


class MCPToolError(ValueError):
    """A safe, user-facing error returned by an MCP tool.

    The MCP package serializes exceptions raised by a tool as protocol errors.  A
    dedicated exception keeps database and serializer implementation details out
    of those errors while retaining useful context for an MCP client.
    """


class WireGuardMCPToolset(MCPToolset):
    """Curated WireGuard UI operations; sensitive peer material is dedicated."""

    def _configuration(self):
        configuration = ServerConfiguration.objects.first()
        if configuration is None:
            raise MCPToolError("Server configuration is not initialized.")
        return configuration

    @staticmethod
    def _get(model, object_id, label):
        try:
            return model.objects.get(pk=object_id)
        except (model.DoesNotExist, ObjectDoesNotExist) as exc:
            raise MCPToolError(f"{label} with id {object_id} was not found.") from exc

    @staticmethod
    def _save_serializer(serializer, label):
        try:
            serializer.is_valid(raise_exception=True)
            return serializer.save()
        except (serializers.ValidationError, ValidationError) as exc:
            raise MCPToolError(f"Invalid {label}: {exc.detail if hasattr(exc, 'detail') else exc}") from exc

    def _safe_peer(self, peer):
        return {
            "id": peer.id,
            "name": peer.name,
            "description": peer.description,
            "email_address": peer.email_address,
            "disabled": peer.disabled,
            "ip_address": peer.ip_address,
            "port": peer.port,
            "public_key": peer.public_key,
            "peer_group_ids": list(peer.peer_groups.values_list("id", flat=True)),
        }

    def _safe_group(self, group):
        return {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "disabled": group.disabled,
            "allow_modify_self": group.allow_modify_self,
            "allow_modify_peers": group.allow_modify_peers,
            "allow_modify_targets": group.allow_modify_targets,
            "peer_ids": list(group.peers.values_list("id", flat=True)),
            "target_ids": list(group.targets.values_list("id", flat=True)),
        }

    def _safe_target(self, target):
        return {
            "id": target.id,
            "name": target.name,
            "description": target.description,
            "disabled": target.disabled,
            "ip_address": target.ip_address,
            "port": target.port,
            "allow_modify_self": target.allow_modify_self,
            "allow_modify_peer_groups": target.allow_modify_peer_groups,
            "peer_group_ids": list(target.peer_groups.values_list("id", flat=True)),
        }

    def list_peers(self):
        return [self._safe_peer(peer) for peer in Peer.objects.all()]

    def retrieve_peer(self, peer_id: int):
        return self._safe_peer(self._get(Peer, peer_id, "Peer"))

    def create_peer(self, body: dict):
        peer = self._save_serializer(PeerWithQrSerializer(data=body), "peer")
        return self._safe_peer(peer)

    def update_peer(self, peer_id: int, body: dict):
        peer = self._get(Peer, peer_id, "Peer")
        peer = self._save_serializer(PeerWithQrSerializer(peer, data=body, partial=True), "peer")
        return self._safe_peer(peer)

    def delete_peer(self, peer_id: int):
        peer = self._get(Peer, peer_id, "Peer")
        result = self._safe_peer(peer)
        peer.delete()
        return result

    def get_peer_configuration(self, peer_id: int):
        peer = self._get(Peer, peer_id, "Peer")
        serializer = PeerWithQrSerializer(peer)
        return {"peer_id": peer.id, "configuration": serializer.data["configuration"]}

    def get_peer_qr(self, peer_id: int):
        peer = self._get(Peer, peer_id, "Peer")
        qr = PeerWithQrSerializer(peer).data["qr"]
        return {"peer_id": peer.id, "qr": qr.decode("ascii") if isinstance(qr, bytes) else qr}

    def list_peer_groups(self):
        return [self._safe_group(group) for group in PeerGroup.objects.all()]

    def retrieve_peer_group(self, group_id: int):
        return self._safe_group(self._get(PeerGroup, group_id, "Peer group"))

    def create_peer_group(self, body: dict):
        group = self._save_serializer(PeerGroupSerializer(data=body), "peer group")
        return self._safe_group(group)

    def update_peer_group(self, group_id: int, body: dict):
        group = self._get(PeerGroup, group_id, "Peer group")
        group = self._save_serializer(PeerGroupSerializer(group, data=body, partial=True), "peer group")
        return self._safe_group(group)

    def delete_peer_group(self, group_id: int):
        group = self._get(PeerGroup, group_id, "Peer group")
        result = self._safe_group(group)
        group.delete()
        return result

    def list_targets(self):
        return [self._safe_target(target) for target in Target.objects.all()]

    def retrieve_target(self, target_id: int):
        return self._safe_target(self._get(Target, target_id, "Target"))

    def create_target(self, body: dict):
        target = self._save_serializer(TargetSerializer(data=body), "target")
        return self._safe_target(target)

    def update_target(self, target_id: int, body: dict):
        target = self._get(Target, target_id, "Target")
        target = self._save_serializer(TargetSerializer(target, data=body, partial=True), "target")
        return self._safe_target(target)

    def delete_target(self, target_id: int):
        target = self._get(Target, target_id, "Target")
        result = self._safe_target(target)
        target.delete()
        return result

    def get_server_configuration(self):
        data = ServerConfigurationSerializer(self._configuration()).data
        data.pop("private_key", None)
        data.pop("mcp_token", None)
        return data

    def update_server_configuration(self, body: dict):
        configuration = self._configuration()
        body = {
            key: value
            for key, value in body.items()
            if key not in {"private_key", "mcp_token", "mcp_enabled"}
        }
        saved = self._save_serializer(
            ServerConfigurationSerializer(configuration, data=body, partial=True),
            "server configuration",
        )
        data = ServerConfigurationSerializer(saved).data
        data.pop("private_key", None)
        data.pop("mcp_token", None)
        return data

    def get_wireguard_configuration(self):
        configuration = self._configuration()
        return WireGuardHelper().get_wireguard_configuration(
            configuration, PeerGroup.objects.all(), Peer.objects.all()
        )

    def generate_wireguard_configuration_files(self):
        """Write WireGuard and IPTables files using the current database state."""
        return generate_configuration_files()

    def restart_wireguard(self):
        """Restart WireGuard immediately; active VPN connections may be interrupted."""
        configuration = self._configuration()
        return {
            "output": WireGuardHelper().restart(serverConfiguration=configuration),
            "warning": "WireGuard was restarted.",
        }

    def get_connected_peers(self):
        return WireGuardHelper().get_connected_peers(Peer.objects.all(), self._configuration())

    def get_server_status(self):
        return get_server_status()

    def get_iptables_log(self):
        return WireGuardHelper().get_iptables_log()

    def get_hierarchy(self):
        return TargetHeirarchySerializer(Target.objects.all(), many=True).data

    def get_license(self):
        with open("/app/LICENSE") as license_file:
            return {"license": license_file.read()}

    def get_application_info(self):
        return get_application_details()

    def send_peer_configuration_email(self, peer_id: int, email_address: str = ""):
        if not IS_EMAIL_ENABLED:
            raise MCPToolError("Email is not enabled on the server.")
        peer = self._get(Peer, peer_id, "Peer")
        configuration = PeerWithQrSerializer(peer).data
        recipient = email_address or peer.email_address
        if not recipient:
            raise MCPToolError("An email address is required.")
        email = EmailMessage(
            subject=f"Tunnel configuration sent from {APP_NAME} for {peer.name}",
            body=f"The WireGuard configuration for {peer.name} is attached. Keep it safe.",
            from_email=settings.EMAIL_HOST_USER,
            to=[recipient],
        )
        email.attach("tunnel.conf", configuration["configuration"], "text/plain")
        email.attach("tunnel.png", base64.b64decode(configuration["qr"]), "image/png")
        try:
            email.send(fail_silently=False)
        except Exception as exc:
            raise MCPToolError("Sending peer configuration email failed.") from exc
        return {"message": "Email sent successfully!"}
