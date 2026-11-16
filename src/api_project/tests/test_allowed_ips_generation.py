import types

from django.test import SimpleTestCase

from api_app.common import PEER_GROUP_EVERYONE_NAME
from api_app.wireguard_helper import WireGuardHelper


def make_server_configuration(**overrides):
    """Build a lightweight fake ServerConfiguration the helper can read."""
    defaults = {
        "upstream_dns_ip_address": "192.168.0.5",
        "network_address": "192.168.3.0/24",
        "ip_address": "192.168.3.1",
        "local_networks": "192.168.0.0/24",
        "strict_allowed_ips_in_peer_config": True,
        "peer_default_port": 51820,
        "host_name_external": "vpn.example.com",
        "port_external": 51820,
        "public_key": "SERVER_PUBLIC_KEY",
        "private_key": "SERVER_PRIVATE_KEY",
    }
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def make_target(ip_address):
    """Build a lightweight fake Target the helper can read."""
    return types.SimpleNamespace(ip_address=ip_address)


def make_peer_group(name, targets=(), peers=()):
    """Build a lightweight fake PeerGroup the helper can read."""
    return types.SimpleNamespace(
        name=name,
        targets=types.SimpleNamespace(all=lambda: list(targets)),
        peers=types.SimpleNamespace(all=lambda: list(peers)),
    )


def make_peer(peer_groups=(), **overrides):
    """Build a lightweight fake Peer the helper can read."""
    defaults = {
        "name": "peer1",
        "public_key": "PEER_PUBLIC_KEY",
        "ip_address": "192.168.3.2",
        "private_key": "PEER_PRIVATE_KEY",
        "port": None,
        "peer_groups": types.SimpleNamespace(all=lambda: list(peer_groups)),
    }
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def allowed_ips_value(client_config):
    """Extract the single AllowedIPs value from the client-side config text."""
    lines = [
        line for line in client_config.splitlines() if line.startswith("AllowedIPs")
    ]
    assert len(lines) == 1, f"expected exactly one AllowedIPs line, got {lines}"
    return lines[0].split("=", 1)[1].strip()


class AllowedIpsGenerationTests(SimpleTestCase):
    """Strict allowed-ips generation must never crash on stored target values."""

    def setUp(self):
        self.helper = WireGuardHelper()

    def client_config(self, peer_groups, peer, server_configuration=None):
        if server_configuration is None:
            server_configuration = make_server_configuration()
        _, client_side = self.helper.get_wireguard_configurations_for_peer(
            server_configuration, peer_groups, peer
        )
        return client_side

    def test_everyone_target_with_port_suffix_generates_route(self):
        # Regression: a ":port" suffix on an EveryOne target used to make
        # allowed_ips.sort() raise TypeError and break every config download.
        everyone = make_peer_group(
            PEER_GROUP_EVERYONE_NAME, targets=[make_target("10.0.0.5:443")]
        )

        client = self.client_config([everyone], make_peer())

        allowed = allowed_ips_value(client)
        self.assertIn("10.0.0.5/32", allowed.split(","))
        self.assertNotIn(":443", allowed)

    def test_unparsable_entry_is_skipped_without_exception(self):
        everyone = make_peer_group(
            PEER_GROUP_EVERYONE_NAME,
            targets=[make_target("nonsense"), make_target("10.0.0.5")],
        )

        client = self.client_config([everyone], make_peer())

        allowed = allowed_ips_value(client)
        self.assertNotIn("nonsense", allowed)
        self.assertIn("10.0.0.5/32", allowed.split(","))

    def test_strict_mode_benign_addresses_emit_exact_expected_value(self):
        group = make_peer_group(
            "group-x",
            targets=[make_target("10.10.0.0/24"), make_target("172.16.5.9")],
            peers=[types.SimpleNamespace(ip_address="192.168.3.7")],
        )
        peer = make_peer(peer_groups=[group])

        client = self.client_config([], peer)

        self.assertEqual(
            allowed_ips_value(client),
            "10.10.0.0/24,172.16.5.9/32,192.168.0.5/32,192.168.3.1/32,"
            "192.168.3.7/32",
        )

    def test_strict_mode_off_keeps_catch_all_fallback(self):
        everyone = make_peer_group(
            PEER_GROUP_EVERYONE_NAME, targets=[make_target("10.0.0.5:443")]
        )
        server_configuration = make_server_configuration(
            strict_allowed_ips_in_peer_config=False
        )

        client = self.client_config(
            [everyone], make_peer(), server_configuration=server_configuration
        )

        self.assertEqual(allowed_ips_value(client), "0.0.0.0/0")
