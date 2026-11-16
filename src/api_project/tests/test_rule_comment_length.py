import shlex
import types

from django.test import SimpleTestCase

from api_app.wireguard_helper import WireGuardHelper

IPTABLES_COMMENT_MAX_BYTES = 256


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


class RuleCommentLengthTests(SimpleTestCase):
    """Generated --comment values must fit the 256-byte iptables limit."""

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

    def comment_token(self, line):
        try:
            tokens = shlex.split(line)
        except ValueError as error:
            self.fail("unbalanced quoting in generated rule: {!r}".format(line))
        self.assertIn("--comment", tokens)
        index = tokens.index("--comment")
        return tokens, index

    def test_max_length_names_stay_within_iptables_comment_limit(self):
        # The regression: three 255-char CharFields produce a 773-byte
        # comment; iptables accepts at most 256 bytes and silently drops
        # the oversized rule, blackholing the peer.
        post_up = self.get_post_up(
            peer_name="a" * 255,
            group_name="b" * 255,
            target_name="c" * 255,
            target_ip_address="10.0.0.7",
        )

        rule_lines = self.get_rule_lines(post_up)
        self.assertTrue(rule_lines)
        own_lines = [line for line in rule_lines if "a" * 200 in line]
        self.assertTrue(
            own_lines,
            "no rule line carried the oversized peer name at all",
        )

        for line in rule_lines:
            tokens, index = self.comment_token(line)
            comment = tokens[index + 1]
            byte_length = len(comment.encode("utf-8"))
            self.assertLessEqual(
                byte_length,
                IPTABLES_COMMENT_MAX_BYTES,
                "comment of {} bytes exceeds the iptables limit: {!r}".format(
                    byte_length, comment
                ),
            )

    def test_oversized_comment_is_a_single_token(self):
        oversized = self.get_post_up(
            peer_name="a" * 255,
            group_name="b" * 255,
            target_name="c" * 255,
            target_ip_address="10.0.0.7",
        )
        benign = self.get_post_up(
            peer_name="peer1",
            group_name="office",
            target_name="net7",
            target_ip_address="10.0.0.7",
        )

        oversized_lines = [
            line for line in self.get_rule_lines(oversized) if "a" * 200 in line
        ]
        benign_lines = [
            line for line in self.get_rule_lines(benign) if "net7" in line
        ]
        self.assertEqual(len(oversized_lines), 1)
        self.assertEqual(len(benign_lines), 1)

        oversized_tokens, index = self.comment_token(oversized_lines[0])
        benign_tokens, _ = self.comment_token(benign_lines[0])

        # exactly one token follows --comment, and the rule is not split:
        # same total token count as the benign rule of identical shape.
        self.assertEqual(len(oversized_tokens), index + 2)
        self.assertEqual(len(oversized_tokens), len(benign_tokens))

    def test_multibyte_names_stay_within_byte_budget(self):
        # "é" is 3 bytes in UTF-8: a character-based slice would leave
        # 200+ characters and blow the 256-byte limit, and cutting a
        # character in half must not raise UnicodeDecodeError.
        post_up = self.get_post_up(
            peer_name="é" * 255,
            group_name="é" * 255,
            target_name="é" * 255,
            target_ip_address="10.0.0.7",
        )

        own_lines = [
            line for line in self.get_rule_lines(post_up) if "é" in line
        ]
        self.assertTrue(own_lines)
        for line in own_lines:
            tokens, index = self.comment_token(line)
            comment = tokens[index + 1]
            self.assertLessEqual(
                len(comment.encode("utf-8")),
                IPTABLES_COMMENT_MAX_BYTES,
                "multi-byte comment exceeds the iptables byte limit",
            )

    def test_benign_comment_is_unchanged(self):
        post_up = self.get_post_up(
            peer_name="peer1",
            group_name="office",
            target_name="Internet",
            target_ip_address="10.0.0.7",
        )

        own_lines = [
            line for line in self.get_rule_lines(post_up) if "Internet" in line
        ]
        self.assertEqual(len(own_lines), 1)
        tokens, index = self.comment_token(own_lines[0])
        self.assertEqual(tokens[index + 1], "peer1 => office => Internet")

    def test_names_below_the_budget_are_not_truncated(self):
        # 50 + 4 + 50 + 4 + 50 = 158 chars, well below the 200-byte cap:
        # the helper is a ceiling, not a shorter cap.
        peer_name = "p" * 50
        group_name = "g" * 50
        target_name = "t" * 50
        post_up = self.get_post_up(
            peer_name=peer_name,
            group_name=group_name,
            target_name=target_name,
            target_ip_address="10.0.0.7",
        )

        own_lines = [
            line for line in self.get_rule_lines(post_up) if peer_name in line
        ]
        self.assertEqual(len(own_lines), 1)
        tokens, index = self.comment_token(own_lines[0])
        self.assertEqual(
            tokens[index + 1],
            "{} => {} => {}".format(peer_name, group_name, target_name),
        )
