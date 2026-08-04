"""Explicit, authenticated MCP tools for the WireGuard administration surface."""

from django.core.exceptions import ObjectDoesNotExist, ValidationError
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
from .shared_functions import (
    get_connected_peers,
    get_iptables_log,
    get_license as read_license,
    get_wireguard_configuration,
    restart_wireguard,
    send_configuration_email,
)


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
        """List all peers from the database.

        Returns a list of dictionaries containing each peer's id, descriptive and
        connection fields, public key, and peer-group ids. Private keys, client
        configurations, and QR data are intentionally excluded. This is a
        read-only database operation.
        """
        return [self._safe_peer(peer) for peer in Peer.objects.all()]

    def retrieve_peer(self, peer_id: int):
        """Retrieve one peer's non-secret database record by integer ``peer_id``.

        Returns the same safe peer dictionary as :meth:`list_peers`. It does not
        return private key material, a generated configuration, or a QR image, and
        it performs no writes.
        """
        return self._safe_peer(self._get(Peer, peer_id, "Peer"))

    def create_peer(self, body: dict):
        """Create a peer from a serializer-compatible ``body`` dictionary.

        The body may include the writable peer fields, including ``peer_group_ids``.
        The model may generate missing WireGuard keys, choose a free VPN address,
        and apply the configured default port. Returns the new safe peer dictionary;
        private key, configuration, and QR data are omitted. This writes the peer
        and its relationships to the database.
        """
        peer = self._save_serializer(PeerWithQrSerializer(data=body), "peer")
        return self._safe_peer(peer)

    def update_peer(self, peer_id: int, body: dict):
        """Partially update a peer identified by integer ``peer_id``.

        ``body`` is validated by the peer serializer and may update writable peer
        fields and group relationships. Returns the updated safe peer dictionary,
        excluding private key, configuration, and QR data. This writes the peer
        record and any requested relationships to the database.
        """
        peer = self._get(Peer, peer_id, "Peer")
        peer = self._save_serializer(PeerWithQrSerializer(peer, data=body, partial=True), "peer")
        return self._safe_peer(peer)

    def delete_peer(self, peer_id: int):
        """Delete the peer identified by integer ``peer_id``.

        Returns the safe peer dictionary captured immediately before deletion.
        This permanently removes the database row and its associated relationship
        records; it is destructive and does not remove already-distributed client
        configuration files or credentials outside the database.
        """
        peer = self._get(Peer, peer_id, "Peer")
        result = self._safe_peer(peer)
        peer.delete()
        return result

    def get_peer_configuration(self, peer_id: int):
        """Return the generated WireGuard client configuration for ``peer_id``.

        Returns ``{"peer_id": int, "configuration": str}``, where the
        configuration contains the peer's private key and connection settings.
        This is highly sensitive credential material: transmit it only to an
        authorized recipient and do not expose or persist it unnecessarily. The
        operation reads the database and derives configuration without changing
        database, filesystem, or WireGuard state.
        """
        peer = self._get(Peer, peer_id, "Peer")
        serializer = PeerWithQrSerializer(peer)
        return {"peer_id": peer.id, "configuration": serializer.data["configuration"]}

    def get_peer_qr(self, peer_id: int):
        """Return a QR-encoded client configuration for ``peer_id``.

        Returns ``{"peer_id": int, "qr": str}``, with ``qr`` containing the
        base64-encoded PNG image generated from the peer configuration. The image
        embeds sensitive WireGuard credential material; treat it like a private
        key and share it only with the intended authorized recipient. This is a
        read-only database/CPU operation with no filesystem or network side effect.
        """
        peer = self._get(Peer, peer_id, "Peer")
        qr = PeerWithQrSerializer(peer).data["qr"]
        return {"peer_id": peer.id, "qr": qr.decode("ascii") if isinstance(qr, bytes) else qr}

    def list_peer_groups(self):
        """List all peer groups and their database relationships.

        Returns a list of dictionaries with ids, names, flags, permissions,
        ``peer_ids``, and ``target_ids``. This performs a read-only database
        operation and does not include generated WireGuard credentials.
        """
        return [self._safe_group(group) for group in PeerGroup.objects.all()]

    def retrieve_peer_group(self, group_id: int):
        """Retrieve one peer group by integer ``group_id``.

        Returns the same group dictionary as :meth:`list_peer_groups`, including
        its permission flags and related peer/target ids. This is read-only and
        does not generate or expose peer credentials.
        """
        return self._safe_group(self._get(PeerGroup, group_id, "Peer group"))

    def create_peer_group(self, body: dict):
        """Create a peer group from a serializer-compatible ``body`` dictionary.

        The body can set group metadata, permission flags, and ``peer_ids`` or
        ``target_ids`` relationships. Returns the created group dictionary. This
        writes the group and requested many-to-many relationships to the database;
        it does not generate files or restart WireGuard.
        """
        group = self._save_serializer(PeerGroupSerializer(data=body), "peer group")
        return self._safe_group(group)

    def update_peer_group(self, group_id: int, body: dict):
        """Partially update a peer group and its requested relationships.

        ``group_id`` identifies the database row and ``body`` is validated by the
        group serializer. Returns the updated group dictionary with peer and target
        ids. This is a database write only; WireGuard files and the active service
        are not regenerated or restarted automatically.
        """
        group = self._get(PeerGroup, group_id, "Peer group")
        group = self._save_serializer(PeerGroupSerializer(group, data=body, partial=True), "peer group")
        return self._safe_group(group)

    def delete_peer_group(self, group_id: int):
        """Delete the peer group identified by integer ``group_id``.

        Returns the group's safe dictionary captured before deletion. This is a
        destructive database operation that removes the group and its relationship
        records; it does not delete the peers or targets themselves, regenerate
        configuration files, or restart WireGuard.
        """
        group = self._get(PeerGroup, group_id, "Peer group")
        result = self._safe_group(group)
        group.delete()
        return result

    def list_targets(self):
        """List all configured targets and their peer-group ids.

        Returns a list of target dictionaries containing ids, descriptive/network
        fields, permission flags, and ``peer_group_ids``. This is a read-only
        database operation and does not contact targets or alter firewall state.
        """
        return [self._safe_target(target) for target in Target.objects.all()]

    def retrieve_target(self, target_id: int):
        """Retrieve one target's database record by integer ``target_id``.

        Returns the same target dictionary as :meth:`list_targets`. No target
        network connection is made and no state is changed.
        """
        return self._safe_target(self._get(Target, target_id, "Target"))

    def create_target(self, body: dict):
        """Create a target from a serializer-compatible ``body`` dictionary.

        The body includes target metadata, network address/port, permission flags,
        and optionally ``peer_group_ids``. Returns the created target dictionary.
        This writes the target and relationships to the database but does not write
        firewall files or restart WireGuard.
        """
        target = self._save_serializer(TargetSerializer(data=body), "target")
        return self._safe_target(target)

    def update_target(self, target_id: int, body: dict):
        """Partially update a target and its requested peer-group relationships.

        ``target_id`` identifies the row and ``body`` is validated by the target
        serializer. Returns the updated target dictionary. This performs a database
        write only; generated firewall files and the active WireGuard service are
        unchanged until another operation regenerates or applies them.
        """
        target = self._get(Target, target_id, "Target")
        target = self._save_serializer(TargetSerializer(target, data=body, partial=True), "target")
        return self._safe_target(target)

    def delete_target(self, target_id: int):
        """Delete the target identified by integer ``target_id``.

        Returns the target dictionary captured before deletion. This is a destructive
        database operation that removes the target and its relationship records;
        it does not regenerate firewall files or restart WireGuard.
        """
        target = self._get(Target, target_id, "Target")
        result = self._safe_target(target)
        target.delete()
        return result

    def get_server_configuration(self):
        """Read the current server configuration without secret fields.

        Returns the serialized server-configuration dictionary with ``private_key``
        and ``mcp_token`` removed. This reads the database only; it does not expose
        those credentials, write configuration, touch files, or change networking.
        """
        data = ServerConfigurationSerializer(self._configuration()).data
        data.pop("private_key", None)
        data.pop("mcp_token", None)
        return data

    def update_server_configuration(self, body: dict):
        """Partially update the server configuration from ``body``.

        The serializer validates writable configuration fields; ``private_key``,
        ``mcp_token``, and ``mcp_enabled`` are always ignored. Returns the updated
        serialized configuration with private key and MCP token removed. This is a
        high-impact database write: changing network or WireGuard settings can
        invalidate addresses/configuration and affect service operation, although
        this method itself does not write generated files or restart WireGuard.
        """
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
        """Generate the complete in-memory WireGuard configuration set.

        Returns ``{"server_configuration": str, "peer_configurations": list[str]}``.
        The server configuration contains private server material and peer entries;
        each peer configuration can contain client private-key credentials. Treat
        the result as highly sensitive and share it only with an authorized user.
        This reads the database and performs template generation only; it does not
        write files, alter firewall rules, or restart WireGuard.
        """
        configuration = self._configuration()
        return get_wireguard_configuration(configuration)

    def generate_wireguard_configuration_files(self):
        """Generate and write WireGuard and iptables files from database state.

        Returns the helper result, normally ``{"status": "ok", "output": str}``.
        This high-impact operation writes files at the configured WireGuard and
        post-up/post-down script paths, changes script permissions using ``sudo chmod``,
        and saves the server configuration object. It does not itself restart
        WireGuard, but the generated files affect later service application and
        contain sensitive VPN configuration.
        """
        return generate_configuration_files()

    def restart_wireguard(self):
        """Immediately restart the configured WireGuard interface.

        Returns ``{"output": {"status": "ok", "output": str}, "warning": str}``.
        This high-impact system operation runs ``wg-quick down``, flushes conntrack,
        and runs ``wg-quick up`` through sudo; active VPN connections may be
        interrupted and network state changes immediately. It reads the database
        for the configured file path and does not modify database records itself.
        """
        configuration = self._configuration()
        return {
            "output": restart_wireguard(configuration),
            "warning": "WireGuard was restarted.",
        }

    def get_connected_peers(self):
        """Inspect live WireGuard peer handshakes and transfer counters.

        Returns a dictionary with a timestamp, ``message``, and ``items`` list.
        Items may include peer name, endpoint IP, allowed IP, connection/inactive
        status, latest handshake, and transfer byte counters. This invokes ``sudo
        wg show all dump`` and therefore reads live system/network state, but does
        not write the database, files, or WireGuard configuration.
        """
        return get_connected_peers(self._configuration())

    def get_server_status(self):
        """Return host, database/file freshness, and WireGuard server status.

        Returns the status dictionary produced by the server helper, including
        platform/hostname information and whether configuration files need
        regeneration. It reads database records and filesystem metadata and invokes
        WireGuard status inspection; it does not write files or change system,
        network, or database state.
        """
        return get_server_status()

    def get_iptables_log(self):
        """Read current IPv4 filter and NAT firewall tables.

        Returns ``{"status": "ok", "datetime": str, "output": str}``, where
        ``output`` is command output from ``sudo iptables -n -L -v --line-numbers``
        and its NAT-table equivalent. This reads live system/network firewall state
        and performs no writes or configuration changes.
        """
        return get_iptables_log()

    def get_hierarchy(self):
        """Return targets serialized with their related hierarchy.

        Returns the target serializer's list of dictionaries, including nested
        related data at serializer depth two, which may contain sensitive peer
        credential fields. Share the result only with an authorized recipient.
        This is a read-only database operation; it does not generate credentials,
        contact targets, or change WireGuard/firewall state.
        """
        return TargetHeirarchySerializer(Target.objects.all(), many=True).data

    def get_license(self):
        """Read and return the application license file.

        Returns ``{"license": str}`` containing the contents of ``/app/LICENSE``.
        This is a filesystem read only and has no database, network, email, or
        system-state side effect.
        """
        return read_license()

    def get_application_info(self):
        """Return application version, update, time, and email capability details.

        Returns the application-details dictionary with current version, latest
        known live version, current time, the ``allow_allow_check_updates`` setting,
        and whether email is enabled. If update checks are enabled and no cached
        version exists, the underlying helper may make an outbound HTTP request and
        update the application cache; it does not alter database or WireGuard state
        directly.
        """
        return get_application_details()

    def send_peer_configuration_email(self, peer_id: int, email_address: str = ""):
        """Email a peer's WireGuard configuration and QR image.

        ``peer_id`` selects the peer; optional ``email_address`` overrides the
        peer's stored address, otherwise that stored address is used. Returns
        ``{"message": "Email sent successfully!"}`` after sending. This sensitive
        operation attaches the peer configuration (including credentials) and a
        QR PNG to an email, so verify the recipient and protect the message. It
        requires email to be enabled, reads the database, and performs an outbound
        email/network side effect; it does not modify the database or WireGuard.
        """
        if not IS_EMAIL_ENABLED:
            raise MCPToolError("Email is not enabled on the server.")
        peer = self._get(Peer, peer_id, "Peer")
        configuration = PeerWithQrSerializer(peer).data
        recipient = email_address or peer.email_address
        if not recipient:
            raise MCPToolError("An email address is required.")
        try:
            send_configuration_email(
                f"Tunnel configuration sent from {APP_NAME} for {peer.name}",
                f"The WireGuard configuration for {peer.name} is attached. Keep it safe.",
                recipient,
                configuration["qr"],
                configuration["configuration"],
            )
        except Exception as exc:
            raise MCPToolError("Sending peer configuration email failed.") from exc
        return {"message": "Email sent successfully!"}
