"""Shared orchestration for the HTTP views and MCP tools."""

import base64

from django.conf import settings
from django.core.mail import EmailMessage

from .models import Peer, PeerGroup, ServerConfiguration
from .wireguardhelper import WireGuardHelper


def get_wireguard_configuration(server_configuration=None):
    """Build the server and peer WireGuard configurations."""
    server_configuration = server_configuration or ServerConfiguration.objects.all()[0]
    return WireGuardHelper().get_wireguard_configuration(
        serverConfiguration=server_configuration,
        peer_groups=PeerGroup.objects.all(),
        peers=Peer.objects.all(),
    )


def restart_wireguard(server_configuration=None):
    """Restart WireGuard using the configured server configuration."""
    server_configuration = server_configuration or ServerConfiguration.objects.all()[0]
    return WireGuardHelper().restart(serverConfiguration=server_configuration)


def get_connected_peers(server_configuration=None, peers=None):
    """Return the live WireGuard connection details for configured peers."""
    server_configuration = server_configuration or ServerConfiguration.objects.all()[0]
    peers = Peer.objects.all() if peers is None else peers
    return WireGuardHelper().get_connected_peers(peers, server_configuration)


def get_iptables_log():
    """Return the current WireGuard firewall log."""
    return WireGuardHelper().get_iptables_log()


def get_license():
    """Read the application license file."""
    with open("/app/LICENSE") as license_file:
        return {"license": license_file.read()}


def send_configuration_email(subject, body, recipient, qr, configuration):
    """Send a peer configuration and QR image as email attachments."""
    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.EMAIL_HOST_USER,
        to=[recipient],
    )
    email.attach("tunnel.conf", configuration, "text/plain")
    email.attach("tunnel.png", base64.b64decode(qr), "image/png")
    email.send(fail_silently=False)
