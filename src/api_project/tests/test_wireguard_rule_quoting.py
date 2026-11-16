import os
import shlex
import shutil
import subprocess
import tempfile
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
        "disabled": False,
        "peer_groups": types.SimpleNamespace(all=lambda: []),
    }
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def make_peer_group(name, peers):
    """Build a lightweight fake PeerGroup the helper can read."""
    return types.SimpleNamespace(
        name=name,
        disabled=False,
        peers=types.SimpleNamespace(all=lambda: list(peers)),
    )


def make_target(name, ip_address, peer_groups):
    """Build a lightweight fake Target the helper can read."""
    return types.SimpleNamespace(
        name=name,
        disabled=False,
        ip_address=ip_address,
        peer_groups=types.SimpleNamespace(all=lambda: list(peer_groups)),
    )


class WireGuardRuleQuotingTests(SimpleTestCase):
    """Stored names/IPs must survive the shell as data, never as syntax."""

    def setUp(self):
        self.helper = WireGuardHelper()

    def get_post_up(self, peer_name, group_name, target_name, target_ip_address):
        peer = make_peer(name=peer_name)
        peer_group = make_peer_group(group_name, [peer])
        target = make_target(target_name, target_ip_address, [peer_group])
        post_up, post_down = self.helper.get_wireguard_iptables_script(
            make_server_configuration(),
            [target],
            [],
            types.SimpleNamespace(all=lambda: []),
        )
        return post_up

    def get_rule_lines(self, post_up):
        return [
            line
            for line in post_up.splitlines()
            if line.startswith("iptables ") and "--comment" in line
        ]

    def test_injected_name_stays_a_single_comment_token(self):
        canary_path = os.path.join(tempfile.gettempdir(), "CANARYPATH-token-check")
        peer_name = 'zz"; touch ' + canary_path + "; #"
        post_up = self.get_post_up(
            peer_name=peer_name,
            group_name="office",
            target_name="filesrv",
            target_ip_address="10.0.0.7",
        )

        rule_lines = self.get_rule_lines(post_up)
        self.assertTrue(rule_lines)
        own_lines = [line for line in rule_lines if "filesrv" in line]
        self.assertEqual(len(own_lines), 1)

        for line in rule_lines:
            try:
                tokens = shlex.split(line)
            except ValueError as error:
                self.fail("unbalanced quoting in generated rule: {!r}".format(line))
            self.assertIn("--comment", tokens)
            index = tokens.index("--comment")
            comment = tokens[index + 1]
            others = tokens[:index] + tokens[index + 2 :]

            if line in own_lines:
                self.assertEqual(comment, "{} => office => filesrv".format(peer_name))
            self.assertNotIn("touch", others)
            self.assertFalse(
                any("CANARYPATH" in token for token in others),
                "canary leaked outside the comment token: {!r}".format(line),
            )

    def test_injected_name_is_not_executed_by_the_shell(self):
        stub_dir = tempfile.mkdtemp()
        canary_dir = tempfile.mkdtemp()
        try:
            stub_path = os.path.join(stub_dir, "iptables")
            with open(stub_path, "w") as f:
                f.write("#!/bin/sh\nexit 0\n")
            os.chmod(stub_path, 0o755)

            canary_path = os.path.join(canary_dir, "CANARY")
            peer_name = 'zz"; touch ' + canary_path + "; #"
            post_up = self.get_post_up(
                peer_name=peer_name,
                group_name="office",
                target_name="filesrv",
                target_ip_address="10.0.0.7",
            )
            own_lines = [
                line
                for line in self.get_rule_lines(post_up)
                if "filesrv" in line
            ]
            self.assertEqual(len(own_lines), 1)

            bash = shutil.which("bash")
            self.assertIsNotNone(bash)
            env = dict(os.environ, PATH=stub_dir)
            result = subprocess.run(
                [bash, "-c", own_lines[0]],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
            self.assertFalse(os.path.exists(canary_path))
        finally:
            shutil.rmtree(stub_dir, ignore_errors=True)
            shutil.rmtree(canary_dir, ignore_errors=True)

    def test_benign_names_are_still_emitted_unchanged(self):
        post_up = self.get_post_up(
            peer_name="peer1",
            group_name="nas",
            target_name="Internet",
            target_ip_address="0.0.0.0/0",
        )

        own_lines = [
            line for line in self.get_rule_lines(post_up) if "Internet" in line
        ]
        self.assertEqual(len(own_lines), 1)
        tokens = shlex.split(own_lines[0])
        index = tokens.index("--comment")

        self.assertEqual(tokens[index + 1], "peer1 => nas => Internet")
        self.assertEqual(
            tokens[: index + 1],
            [
                "iptables",
                "-w5",
                "--append",
                "FORWARD",
                "--source",
                "192.168.3.2",
                "--dest",
                "0.0.0.0/0",
                "-j",
                "ACCEPT",
                "-m",
                "comment",
                "--comment",
            ],
        )
