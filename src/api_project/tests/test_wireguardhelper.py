import types

from django.test import SimpleTestCase

from api_app.wireguardhelper import WireGuardHelper


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
        "public_key": "SERVER_PUBLIC_KEY",
        "private_key": "",
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


class WireGuardIptablesScriptTests(SimpleTestCase):
    def setUp(self):
        self.helper = WireGuardHelper()
        self.server_configuration = make_server_configuration()
        self.targets = []
        self.peer_groups = []
        self.peers = types.SimpleNamespace(all=lambda: [])

    def get_scripts(self):
        return self.helper.get_wireguard_iptables_script(
            self.server_configuration,
            self.targets,
            self.peer_groups,
            self.peers,
        )

    def test_post_up_does_not_full_flush_tables(self):
        post_up, post_down = self.get_scripts()
        self.assertNotIn("iptables --table nat --flush", post_up)
        self.assertNotIn("iptables --delete-chain", post_up)
        self.assertNotIn("iptables --flush", post_up)
        self.assertIn("iptables -w5 --table filter --flush FORWARD", post_up)

    def test_post_up_dns_dnat_is_scoped_to_wireguard_interface(self):
        post_up, post_down = self.get_scripts()
        self.assertIn(
            "PREROUTING --in-interface ${WIREGUARD_INTERFACE} --protocol udp --destination-port 53 --jump DNAT --to-destination 192.168.0.5:53",
            post_up,
        )
        self.assertIn(
            "PREROUTING --in-interface ${WIREGUARD_INTERFACE} --protocol tcp --destination-port 53 --jump DNAT --to-destination 192.168.0.5:53",
            post_up,
        )

    def test_post_up_allows_udp_and_tcp_dns_forwarding(self):
        post_up, post_down = self.get_scripts()
        self.assertIn(
            "FORWARD --in-interface ${WIREGUARD_INTERFACE} -p udp -m udp --dport 53 -j ACCEPT",
            post_up,
        )
        self.assertIn(
            "FORWARD --in-interface ${WIREGUARD_INTERFACE} -p tcp -m tcp --dport 53 -j ACCEPT",
            post_up,
        )

    def test_post_up_masquerade_preserved(self):
        post_up, post_down = self.get_scripts()
        self.assertIn("MASQUERADE", post_up)

    def test_post_down_is_targeted(self):
        post_up, post_down = self.get_scripts()
        self.assertIn("iptables -w5 --table filter --flush FORWARD", post_down)
        self.assertNotIn("iptables --table nat --flush", post_down)
        self.assertNotIn("iptables --delete-chain", post_down)
        self.assertIn("WIREGUARD_INTERFACE=wg0", post_down)

    def test_strict_allowed_ips_includes_upstream_dns(self):
        server_configuration = make_server_configuration(
            strict_allowed_ips_in_peer_config=True
        )
        peer = make_peer()
        server_side_config, client_side_config = (
            self.helper.get_wireguard_configurations_for_peer(
                server_configuration, [], peer
            )
        )
        self.assertIn("192.168.0.5/32", client_side_config)

    def test_generated_commands_use_xtables_lock_wait(self):
        post_up, post_down = self.get_scripts()
        self.assertIn("iptables -w5", post_up)
        for line in post_up.splitlines():
            if line.startswith("iptables "):
                self.assertTrue(
                    line.startswith("iptables -w5"),
                    "iptables command missing -w5: {!r}".format(line),
                )
