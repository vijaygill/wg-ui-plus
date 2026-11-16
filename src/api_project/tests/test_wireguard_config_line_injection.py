import types

from django.test import SimpleTestCase

from api_app.wireguard_helper import WireGuardHelper


def make_server_configuration(**overrides):
    """Build a lightweight fake ServerConfiguration the helper can read."""
    defaults = {
        "upstream_dns_ip_address": "192.168.0.5",
        "network_address": "192.168.3.0/24",
        "ip_address": "192.168.3.1",
        "local_networks": "192.168.0.0/24",
        "strict_allowed_ips_in_peer_config": False,
        "peer_default_port": 51820,
        "host_name_external": "vpn.example.com",
        "port_external": 51820,
        "port_internal": 51820,
        "public_key": "SERVER_PUBLIC_KEY",
        "private_key": "SERVER_PRIVATE_KEY",
        "wireguard_config_path": "/config/wireguard/wg0.conf",
        "script_path_post_up": "/config/post-up.sh",
        "script_path_post_down": "/config/post-down.sh",
    }
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def make_peer(**overrides):
    """Build a lightweight fake Peer the helper can read."""
    defaults = {
        "name": "peer1",
        "public_key": "PEER_PUBLIC_KEY",
        "ip_address": "192.168.3.2",
        "private_key": "PEER_PRIVATE_KEY",
        "port": None,
        "peer_groups": types.SimpleNamespace(all=lambda: []),
    }
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


class WireGuardConfigLineInjectionTests(SimpleTestCase):
    """A stored value must never add a line to the generated ini text."""

    def setUp(self):
        self.helper = WireGuardHelper()

    def get_server_config(self, **overrides):
        return self.helper.get_wireguard_configuration_for_server(
            make_server_configuration(**overrides), []
        )

    def get_client_config(self, **overrides):
        server_configuration = make_server_configuration(**overrides)
        _, client_side = self.helper.get_wireguard_configurations_for_peer(
            server_configuration, [], make_peer()
        )
        return client_side

    def get_peer_configs(self, **peer_overrides):
        """Render both peer fragments for a peer with the given field values."""
        return self.helper.get_wireguard_configurations_for_peer(
            make_server_configuration(), [], make_peer(**peer_overrides)
        )

    def directives(self, generated):
        """Lines that wg-quick would treat as a PostUp/PostDown directive."""
        return [
            line
            for line in generated.splitlines()
            if line.strip().startswith(("PostUp", "PostDown"))
        ]

    def test_post_up_value_cannot_add_a_second_post_up_line(self):
        payload = "\nPostUp = id"
        generated = self.get_server_config(
            script_path_post_up="/config/post-up.sh" + payload
        )

        post_up_lines = [
            line for line in generated.splitlines() if line.startswith("PostUp")
        ]
        self.assertEqual(len(post_up_lines), 1)
        self.assertNotIn(payload, generated)

    def test_post_down_value_cannot_add_a_second_post_down_line(self):
        payload = "\nPostDown = id"
        generated = self.get_server_config(
            script_path_post_down="/config/post-down.sh" + payload
        )

        post_down_lines = [
            line for line in generated.splitlines() if line.startswith("PostDown")
        ]
        self.assertEqual(len(post_down_lines), 1)
        self.assertNotIn(payload, generated)

    def test_host_name_cannot_add_a_line_to_peer_config(self):
        payload = "\nPostUp = id"
        generated = self.get_client_config(
            host_name_external="vpn.example.com" + payload
        )

        endpoint_lines = [
            line for line in generated.splitlines() if line.startswith("Endpoint")
        ]
        self.assertEqual(len(endpoint_lines), 1)
        self.assertNotIn(payload, generated)
        self.assertEqual(
            [line for line in generated.splitlines() if line.startswith("PostUp")],
            [],
        )

    def test_benign_values_are_emitted_unchanged(self):
        server_config = self.get_server_config()
        client_config = self.get_client_config()

        self.assertIn("PostUp = /config/post-up.sh", server_config.splitlines())
        self.assertIn("PostDown = /config/post-down.sh", server_config.splitlines())
        self.assertIn("Endpoint = vpn.example.com:51820", client_config.splitlines())

    def test_peer_ip_address_cannot_add_a_line_to_client_config(self):
        payload = "\nPostUp = touch /tmp/should-not-run"
        benign = self.get_client_config()
        _, injected = self.get_peer_configs(ip_address="192.168.3.9" + payload)

        address_lines = [
            line for line in injected.splitlines() if line.startswith("Address")
        ]
        self.assertEqual(len(address_lines), 1)
        self.assertEqual(self.directives(injected), [])
        self.assertEqual(len(injected.splitlines()), len(benign.splitlines()))

    def test_peer_name_cannot_add_a_line_to_server_side_config(self):
        payload = "\nPostUp = touch /tmp/should-not-run"
        server_side, _ = self.get_peer_configs(name="laptop" + payload)

        self.assertEqual(self.directives(server_side), [])
        self.assertEqual(
            len([line for line in server_side.splitlines() if line == "[Peer]"]), 1
        )

    def test_peer_fragments_are_emitted_unchanged(self):
        server_side, client_side = self.get_peer_configs()

        self.assertEqual(
            server_side,
            """
# Server-side settings for the client.
# peer1
[Peer]
PublicKey = PEER_PUBLIC_KEY
AllowedIPs = 192.168.3.2/32
PersistentKeepalive = 25
#PresharedKey = <this is optional>

""",
        )
        self.assertEqual(
            client_side,
            """
# Settings for this client.
[Interface]
Address = 192.168.3.2
ListenPort = 51820
PrivateKey = PEER_PRIVATE_KEY
DNS = 192.168.0.5

# Settings for the peer on the server side.
[Peer]
PublicKey = SERVER_PUBLIC_KEY
Endpoint = vpn.example.com:51820
AllowedIPs = 0.0.0.0/0
""",
        )

    def test_injected_directive_never_starts_a_line_in_either_fragment(self):
        payload = "\nPostUp = touch /tmp/should-not-run"
        server_side, client_side = self.get_peer_configs(
            name="laptop" + payload, ip_address="192.168.3.9" + payload
        )

        for generated in (server_side, client_side):
            self.assertEqual(self.directives(generated), [])
