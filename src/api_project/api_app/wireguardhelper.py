#!/usr/bin/python
import os
import datetime
import ipaddress
from functools import wraps
import random
import pathlib
import codecs
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives import serialization
import qrcode
import subprocess
import re
import logging
from django.template import Template, Context
from django.utils import timezone

from .common import PEER_GROUP_EVERYONE_NAME, IP_ADDRESS_INTERNET

logger = logging.getLogger(__name__)


def logged(func):
    @wraps(func)
    def logger_func(*args, **kwargs):
        func_name = func.__name__
        try:
            logger.debug(f"{func_name}: start")
            res = func(*args, **kwargs)
            return res
        finally:
            logger.debug(f"{func_name}: end")

    return logger_func


def is_network_address(addr):
    ip = ipaddress.ip_interface(str(addr))
    if isinstance(addr, (ipaddress.IPv4Interface)):
        ip = addr
    res = int(ip.ip) == int(ip.network.network_address) and ip.network.prefixlen < 32
    return (res, ip.ip, ip.network)


def ensure_folder_exists_for_file(filepath):
    dir = os.path.dirname(filepath)
    if not os.path.exists(dir):
        os.makedirs(dir)
        logger.warning(f"Directory was missing. Created: {dir}")


def generate_keys():
    # generate private key
    private_key = X25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    key_private = codecs.encode(private_bytes, "base64").decode("utf8").strip()

    # derive public key
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )
    key_public = codecs.encode(public_bytes, "base64").decode("utf8").strip()
    return (key_public, key_private)


class WireGuardHelper(object):

    @logged
    def render_template(self, template, context):
        template = Template(template)
        res = template.render(context)
        return res

    @logged
    def getWireguardConfigurationForServer(self, serverConfiguration):
        template = """
# Settings for Server.
[Interface]
Address = {{serverConfiguration.network_address}}
ListenPort = {{serverConfiguration.port_internal}}
PrivateKey = {{serverConfiguration.private_key}}

PostUp = {{serverConfiguration.script_path_post_up}}
PostDown = {{serverConfiguration.script_path_post_down}}

"""
        context = Context({"serverConfiguration": serverConfiguration})
        res = self.render_template(template, context)
        return res

    @logged
    def getWireguardConfigurationsForPeer(self, serverConfiguration, peer):
        # returns tuple of server-side and client-side configurations
        template_disabled = """
# Server-side settings for the client.
# {{peer.name}}: disabled
"""
        template = """
# Server-side settings for the client.
# {{peer.name}}
[Peer]
PublicKey = {{peer.public_key}}
AllowedIPs = {{peer.ip_address}}/32
PersistentKeepalive = 25
#PresharedKey = <this is optional>

"""
        context = Context({"peer": peer})
        peer_config_server_side = (
            self.render_template(template_disabled, context)
            if peer.disabled
            else self.render_template(template, context)
        )

        template_disabled = """
# Client-side settings for the peer on the other side of the pipe.
# {{peer.name}}: disabled

"""

        template = """
# Settings for this client.
[Interface]
Address = {{peer.ip_address}}
ListenPort = {{peer_port}}
PrivateKey = {{peer.private_key}}
DNS = {{serverConfiguration.upstream_dns_ip_address}}


# Settings for the peer on the other side of the pipe.
[Peer]
PublicKey = {{serverConfiguration.public_key}}
Endpoint = {{serverConfiguration.host_name_external}}:{{serverConfiguration.port_external}}
AllowedIPs = 0.0.0.0/0
"""
        peer_port = peer.port if peer.port else serverConfiguration.peer_default_port
        context = Context(
            {
                "serverConfiguration": serverConfiguration,
                "peer": peer,
                "peer_port": peer_port,
            }
        )
        peer_config_client_side = (
            self.render_template(template_disabled, context)
            if peer.disabled
            else self.render_template(template, context)
        )

        res = (peer_config_server_side, peer_config_client_side)
        return res

    @logged
    def getWireguardConfiguration(self, serverConfiguration, peers):

        server_config = self.getWireguardConfigurationForServer(serverConfiguration)

        # now generate configs for peers
        # both for the server side and client side
        peer_configs = []
        for peer in peers:
            peer_config_server_side, peer_config_client_side = (
                self.getWireguardConfigurationsForPeer(serverConfiguration, peer)
            )
            server_config += peer_config_server_side
            peer_configs += [peer_config_client_side]

        res = {}
        res["server_configuration"] = server_config
        res["peer_configurations"] = peer_configs
        return res

    def get_chain_name(self, target):
        res = re.sub(r"[^a-zA-Z0-9]", "", str(target.name))
        return res

    @logged
    def getWireguardIpTablesScript(
        self, serverConfiguration, targets, peer_groups, peers
    ):
        dns_servers = [serverConfiguration.upstream_dns_ip_address]
        vpn_network_address = ipaddress.ip_interface(
            serverConfiguration.network_address
        ).network
        internet__network_address = ipaddress.ip_interface(IP_ADDRESS_INTERNET).network
        # generate post-up script
        post_up = [
            "#!/bin/bash",
            "WIREGUARD_INTERFACE=wg0",
            f"WIREGUARD_LAN={vpn_network_address}",
            "LAN_INTERFACE=eth0",
            'echo "***** PostUp: Configuration ******************** "',
            'echo "WIREGUARD_LAN: ${WIREGUARD_LAN}"',
            'echo "LAN_INTERFACE: ${LAN_INTERFACE}"',
            'echo "************************************************ "',
            "",
            "# clear existing rules and setup defaults",
            "iptables --flush",
            "iptables --table nat --flush",
            "iptables --delete-chain",
            "",
            "",
            "# masquerade traffic related to wg0",
            "iptables -t nat -I POSTROUTING -o ${LAN_INTERFACE} -j MASQUERADE -s $WIREGUARD_LAN",
            "",
            "# Accept related or established traffic",
            'iptables -A FORWARD -m state --state RELATED,ESTABLISHED -j ACCEPT -m comment --comment "Established and related packets."',
            "",
        ]

        for dns_server in dns_servers:
            rules = [
                "# now make all DNS traffic flow to desired DNS server",
                f"iptables -t nat -I PREROUTING -p udp --dport 53 -j DNAT --to {dns_server}:53",
                "",
            ]
            post_up += rules

        target_infos = []
        for target in targets:
            for peer_group in target.peer_groups.all():
                if peer_group.name == PEER_GROUP_EVERYONE_NAME:
                    continue
                (
                    target_is_network_address,
                    target_ip_address,
                    target_network_address,
                ) = is_network_address(target.ip_address)
                peer_infos = [
                    (
                        x.name,
                        x.disabled,
                        x.ip_address,
                    )
                    for x in peer_group.peers.all()
                ]
                target_infos += [
                    (
                        self.get_chain_name(target),
                        target.name,
                        target.disabled,
                        target_is_network_address,
                        target_ip_address,
                        target_network_address,
                        peer_group.name,
                        peer_group.disabled,
                        peer_infos,
                    )
                ]

        peer_group_everyone = [
            x for x in peer_groups if x.name == PEER_GROUP_EVERYONE_NAME
        ]
        if peer_group_everyone:
            peer_group_everyone = peer_group_everyone[0]
        if peer_group_everyone:
            for target in peer_group_everyone.targets.all():
                (
                    target_is_network_address,
                    target_ip_address,
                    target_network_address,
                ) = is_network_address(target.ip_address)
                peer_infos = [
                    (
                        x.name,
                        x.disabled,
                        x.ip_address,
                    )
                    for x in peers.all()
                ]
                target_infos += [
                    (
                        self.get_chain_name(target),
                        target.name,
                        target.disabled,
                        target_is_network_address,
                        target_ip_address,
                        target_network_address,
                        peer_group_everyone.name,
                        peer_group_everyone.disabled,
                        peer_infos,
                    )
                ]

        # allow all DNS traffic
        post_up += [
            'iptables --append FORWARD -p udp -m udp --dport 53 -j ACCEPT -m comment --comment "ALLOW - All DNS traffic"',
        ]

        # now add FORWARD and ACCEPT rules for each chain - hosts only
        for (
            chain_name,
            target_name,
            target_disabled,
            target_is_network_address,
            target_ip_address,
            target_network_address,
            peer_group_name,
            peer_group_disabled,
            peer_infos,
        ) in target_infos:
            if target_is_network_address:
                continue
            for peer_name, peer_disabled, peer_ip_address in peer_infos:
                post_up += [
                    f'iptables --append FORWARD --source {peer_ip_address} --dest {target_ip_address} -j ACCEPT -m comment --comment "{peer_name} ({peer_ip_address}) => {peer_group_name} => {target_name}"',
                ]

        # add FORWARD and ACCEPT rules for each chain - networks only but NOT INTERNET!
        for (
            chain_name,
            target_name,
            target_disabled,
            target_is_network_address,
            target_ip_address,
            target_network_address,
            peer_group_name,
            peer_group_disabled,
            peer_infos,
        ) in target_infos:
            if not target_is_network_address:
                continue
            if target_network_address == internet__network_address:
                continue
            for peer_name, peer_disabled, peer_ip_address in peer_infos:
                post_up += [
                    f'iptables --append FORWARD --source {peer_ip_address} --dest {target_network_address} -j ACCEPT -m comment --comment "{peer_name} ({peer_ip_address}) => {peer_group_name} => {target_name}"',
                ]

        local_networks = []
        if serverConfiguration.local_networks:
            local_networks = [
                x for x in serverConfiguration.local_networks.split(",") if x
            ]
        targets_to_block = local_networks #+ [str(vpn_network_address)]
        post_up += [
            f'iptables --append FORWARD --destination {target} -j DROP -m comment --comment "DROP - Everything going to local network - {target}"'
            for target in targets_to_block
        ]

        # add FORWARD and ACCEPT rules for each chain - networks only INTERNET!
        for (
            chain_name,
            target_name,
            target_disabled,
            target_is_network_address,
            target_ip_address,
            target_network_address,
            peer_group_name,
            peer_group_disabled,
            peer_infos,
        ) in target_infos:
            if not target_is_network_address:
                continue
            if target_network_address != internet__network_address:
                continue
            for peer_name, peer_disabled, peer_ip_address in peer_infos:
                post_up += [
                    f'iptables --append FORWARD --source {peer_ip_address} --dest {target_network_address} -j ACCEPT -m comment --comment "{peer_name} ({peer_ip_address}) => {peer_group_name} => {target_name}"',
                ]

        post_up += [
            'iptables -A FORWARD -j DROP -m comment --comment "DROP - everything else"',
        ]

        post_up += ["\n", "iptables -n -L -v --line-numbers;", "\n"]

        post_up = "\n".join(post_up)

        post_down = [
            f"iptables --flush",
            f"iptables --table nat --flush",
            f"iptables --delete-chain",
            f"",
            f"iptables -n -L -v --line-numbers",
        ]

        post_down = "\n".join(post_down)

        return (post_up, post_down)

    @logged
    def generateConfigurationFiles(
        self, serverConfiguration, targets, peer_groups, peers
    ):

        # first save wg0.conf
        ensure_folder_exists_for_file(serverConfiguration.wireguard_config_path)
        configs = self.getWireguardConfiguration(
            serverConfiguration=serverConfiguration, peers=peers
        )
        with open(serverConfiguration.wireguard_config_path, "w") as f:
            server_config = configs["server_configuration"]
            f.write(f"{server_config}\n")

        # save post-up/post-down scripts
        ensure_folder_exists_for_file(serverConfiguration.script_path_post_up)
        ensure_folder_exists_for_file(serverConfiguration.script_path_post_down)
        iptables_scripts_post_up, iptables_scripts_post_down = (
            self.getWireguardIpTablesScript(
                serverConfiguration=serverConfiguration,
                targets=targets,
                peer_groups=peer_groups,
                peers=peers,
            )
        )
        with open(serverConfiguration.script_path_post_up, "w") as f:
            f.write(f"{iptables_scripts_post_up}\n")
        with open(serverConfiguration.script_path_post_down, "w") as f:
            f.write(f"{iptables_scripts_post_down}\n")
        output1 = self.execute_process(
            f"sudo chmod +x {serverConfiguration.script_path_post_up}"
        )
        output2 = self.execute_process(
            f"sudo chmod +x {serverConfiguration.script_path_post_down}"
        )
        res = {"status": "ok", "output": output1 + "\n" + output2}
        return res

    @logged
    def execute_process(self, command):
        output = ""
        proc = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        try:
            outs, errs = proc.communicate(timeout=60)
            output = outs.decode("utf-8") + errs.decode("utf-8")
        except subprocess.TimeoutExpired:
            proc.kill()
        res = output
        logger.debug(output)
        return res

    @logged
    def restart(self, serverConfiguration):
        sc = serverConfiguration
        command = f"sudo wg-quick down {sc.wireguard_config_path}; sudo wg-quick up {sc.wireguard_config_path}; sudo conntrack -F; sudo conntrack -F; sudo conntrack -F;"
        output = self.execute_process(command)
        res = {"status": "ok", "output": output}
        return res

    @logged
    def get_connected_peers(self, peers):
        regex = r"""
            (?P<interface> wg\d+) \s+
                        (?P<public_key> [^\s]+) \s+
                        (?P<preshared_key> [^\s]+) \s+
            (?P<endpoint>
                        (?P<end_point_ip> \d+\.\d+\.\d+\.\d+ ) : (?P<end_point_port> \d+ | \(none\)) | \(none\)) \s+
                        (?P<allowed_ips> \d+\.\d+\.\d+\.\d+\/\d+) \s+
                        (?P<latest_handshake> \d+) \s+
                        (?P<transfer_rx> \d+) \s+
                        (?P<transfer_tx> \d+) \s+
                        (?P<persistent_keepalive> \d+) \s+
            """
        regex = r"""
            (?P<interface> wg\d+) \s+
                        (?P<public_key> [^\s]+) \s+
                        (?P<preshared_key> [^\s]+) \s+
            (?P<endpoint>
                        (?P<end_point_ip> \d+\.\d+\.\d+\.\d+ ) : (?P<end_point_port> \d+ | \(none\)) | \(none\)) \s+
                        (?P<allowed_ips> (?P<allowed_ips_ip>\d+\.\d+\.\d+\.\d+) / (?P<allowed_ips_mask>\d+) ) \s+
                        (?P<latest_handshake> \d+) \s+
                        (?P<transfer_rx> \d+) \s+
                        (?P<transfer_tx> \d+) \s+
                        (?P<persistent_keepalive> \d+) \s+
            """
        output = self.execute_process("sudo wg show all dump;")
        matches = re.finditer(regex, output, re.MULTILINE | re.IGNORECASE | re.VERBOSE)
        dt = datetime.datetime.now().astimezone()
        res = {}
        res["datetime"] = dt.strftime("%Y-%m-%d %H:%M:%S")
        res["items"] = []
        for match_num, match in enumerate(matches, start=1):
            peer_data = match.groupdict()
            peers_filtered = [
                x for x in peers if x.public_key == peer_data["public_key"]
            ]
            peer = peers_filtered[0] if peers_filtered else None
            peer_data["public_key"] = ""
            if peer:
                peer_data["peer_name"] = peer.name
            else:
                peer_data["peer_name"] = f"unknown-{match_num}"
            if "latest_handshake" in peer_data.keys():
                peer_data["latest_handshake"] = str(
                    datetime.datetime.fromtimestamp(int(peer_data["latest_handshake"]))
                    .astimezone(tz=dt.tzinfo)
                    .strftime("%Y-%m-%d %H:%M:%S")
                )
            peer_data["is_connected"] = False
            if "end_point_ip" in peer_data.keys() and peer_data["end_point_ip"]:
                peer_data["is_connected"] = True
            else:
                peer_data["end_point"] = None
            res["items"] += [peer_data]
        return res
