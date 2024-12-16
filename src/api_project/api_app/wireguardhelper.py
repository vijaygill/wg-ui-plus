#!/usr/bin/python
import os
import glob
import datetime
import ipaddress
import subprocess
import re
import socket
import platform

from django.template import Template, Context
from django.utils import timezone

from .common import (
    PEER_GROUP_EVERYONE_NAME,
    IP_ADDRESS_INTERNET,
    MAX_LAST_HANDSHAKE_SECONDS,
    logged,
    logger,
)
from .util import (
    ensure_folder_exists_for_file,
    get_target_ip_address_parts,
    is_network_address,
)


class WireGuardHelper(object):

    @logged
    def render_template(self, template, context):
        template = Template(template)
        res = template.render(context)
        return res

    @logged
    def get_wireguard_configuration_for_server(self, serverConfiguration, peers):
        template = """
# Settings for Server.
[Interface]
Address = {{server_ip_address}}
ListenPort = {{serverConfiguration.port_internal}}
PrivateKey = {{serverConfiguration.private_key}}

PostUp = {{serverConfiguration.script_path_post_up}}
PostDown = {{serverConfiguration.script_path_post_down}}

"""
        context = Context(
            {
                "serverConfiguration": serverConfiguration,
                "server_ip_address": serverConfiguration.ip_address,
            }
        )
        res = self.render_template(template, context)
        return res

    @logged
    def get_wireguard_configurations_for_peer(
        self, serverConfiguration, peer_groups, peer
    ):
        # returns tuple of server-side and client-side configurations
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
        peer_config_server_side = self.render_template(template, context)

        peer_group_everyone = [
            x for x in peer_groups if x.name == PEER_GROUP_EVERYONE_NAME
        ]

        allowed_ips = [IP_ADDRESS_INTERNET]

        if serverConfiguration.strict_allowed_ips_in_peer_config:
            allowed_ips = []

            allowed_ips_everyone = []
            if peer_group_everyone:
                allowed_ips_everyone = [
                    x.ip_address for x in peer_group_everyone[0].targets.all()
                ]

            allowed_ips_by_peer_groups = [
                p.ip_address.split(":")[0]
                for pg in peer.peer_groups.all()
                for p in pg.peers.all()
                if p.ip_address and p.ip_address != peer.ip_address
            ]

            allowed_ips_by_targets = [
                target.ip_address.split(":")[0]
                for pg in peer.peer_groups.all()
                for target in pg.targets.all()
                if target.ip_address
            ]

            allowed_ips = (
                allowed_ips_everyone
                + allowed_ips_by_peer_groups
                + allowed_ips_by_targets
            )

            # # add upstream DNS server to allowed IP's.
            # if serverConfiguration.upstream_dns_ip_address:
            #     allowed_ips += [serverConfiguration.upstream_dns_ip_address]

            # add VPN server's ip address also.
            if serverConfiguration.network_address:
                allowed_ips += [serverConfiguration.ip_address]

        # if 0.0.0.0/0 is in the list, no need to have anything else.
        if IP_ADDRESS_INTERNET in allowed_ips:
            allowed_ips = [IP_ADDRESS_INTERNET]

        allowed_ips = list(set(allowed_ips))

        # if there is no allowedIPs, default to catch-all
        if not allowed_ips:
            allowed_ips = [IP_ADDRESS_INTERNET]

        logger.debug(
            f"serverConfiguration.strict_allowed_ips_in_peer_config: {serverConfiguration.strict_allowed_ips_in_peer_config} => allowed_ips: {allowed_ips}"
        )

        allowed_ips = [is_network_address(x) for x in allowed_ips]
        allowed_ips = [x[2] for x in allowed_ips]
        allowed_ips.sort()
        allowed_ips = [str(x) for x in allowed_ips]

        allowed_ips = ",".join(allowed_ips)

        template = """
# Settings for this client.
[Interface]
Address = {{peer.ip_address}}
ListenPort = {{peer_port}}
PrivateKey = {{peer.private_key}}
DNS = {{serverConfiguration.upstream_dns_ip_address}}

# Settings for the peer on the server side.
[Peer]
PublicKey = {{serverConfiguration.public_key}}
Endpoint = {{serverConfiguration.host_name_external}}:{{serverConfiguration.port_external}}
AllowedIPs = {{allowed_ips}}
"""
        peer_port = peer.port if peer.port else serverConfiguration.peer_default_port
        context = Context(
            {
                "serverConfiguration": serverConfiguration,
                "peer": peer,
                "peer_port": peer_port,
                "allowed_ips": allowed_ips,
            }
        )
        peer_config_client_side = self.render_template(template, context)

        res = (peer_config_server_side, peer_config_client_side)
        return res

    @logged
    def get_wireguard_configuration(self, serverConfiguration, peer_groups, peers):

        server_config = self.get_wireguard_configuration_for_server(
            serverConfiguration, peers
        )

        # now generate configs for peers
        # both for the server side and client side
        peer_configs = []
        for peer in peers:
            peer_config_server_side, peer_config_client_side = (
                self.get_wireguard_configurations_for_peer(
                    serverConfiguration, peer_groups, peer
                )
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
    def get_wireguard_iptables_script(
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
            post_up += [
                "# now make all DNS traffic flow to desired DNS server",
                f"iptables -t nat -I PREROUTING -p udp --dport 53 -j DNAT --to {dns_server}:53",
                f"iptables -t nat -I PREROUTING -p tcp --dport 53 -j DNAT --to {dns_server}:53",
                "",
            ]

        target_infos = []
        for target in targets:
            for peer_group in target.peer_groups.all():
                if peer_group.name == PEER_GROUP_EVERYONE_NAME:
                    continue
                (
                    is_valid,
                    target_is_network_address,
                    target_ip_address,
                    target_network_address,
                    target_port,
                    target_mask,
                    errors,
                ) = get_target_ip_address_parts(target.ip_address)
                peer_infos = sorted(
                    [
                        (
                            x.name,
                            x.disabled,
                            x.ip_address,
                        )
                        for x in peer_group.peers.all()
                    ],
                    key=lambda x: x[0],
                )
                target_infos += [
                    (
                        self.get_chain_name(target),
                        target.name,
                        target.disabled,
                        target_is_network_address,
                        target_ip_address,
                        target_network_address,
                        target_port,
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
                    is_valid,
                    target_is_network_address,
                    target_ip_address,
                    target_network_address,
                    target_port,
                    target_mask,
                    errors,
                ) = get_target_ip_address_parts(target.ip_address)
                peer_infos = sorted(
                    [
                        (
                            x.name,
                            x.disabled,
                            x.ip_address,
                        )
                        for x in peers.all()
                    ],
                    key=lambda x: x[0],
                )
                target_infos += [
                    (
                        self.get_chain_name(target),
                        target.name,
                        target.disabled,
                        target_is_network_address,
                        target_ip_address,
                        target_network_address,
                        target_port,
                        peer_group_everyone.name,
                        peer_group_everyone.disabled,
                        peer_infos,
                    )
                ]

        # filter out disabled targets/peer-groups/peers
        target_infos = [
            (
                chain_name,
                target_name,
                target_disabled,
                target_is_network_address,
                target_ip_address,
                target_network_address,
                target_port,
                peer_group_name,
                peer_group_disabled,
                peer_infos,
            )
            for (
                chain_name,
                target_name,
                target_disabled,
                target_is_network_address,
                target_ip_address,
                target_network_address,
                target_port,
                peer_group_name,
                peer_group_disabled,
                peer_infos,
            ) in target_infos
            if not target_disabled and not peer_group_disabled
        ]

        # sort items
        target_infos = sorted(target_infos, key=lambda x: (x[1], x[7]))

        # allow all DNS traffic
        post_up.append(
            'iptables --append FORWARD -p udp -m udp --dport 53 -j ACCEPT -m comment --comment "ALLOW - All DNS traffic"'
        )

        # now add FORWARD and ACCEPT rules for each chain - hosts only
        for (
            chain_name,
            target_name,
            target_disabled,
            target_is_network_address,
            target_ip_address,
            target_network_address,
            target_port,
            peer_group_name,
            peer_group_disabled,
            peer_infos,
        ) in target_infos:
            if target_is_network_address:
                continue
            for peer_name, peer_disabled, peer_ip_address in peer_infos:
                if str(target_ip_address) == str(serverConfiguration.ip_address):
                    # no need to add rule for peer => server
                    # as all packets have to go via server anyway
                    continue
                if peer_disabled:
                    post_up.append(
                        f'iptables --append FORWARD --source {peer_ip_address} -j DROP -m comment --comment "{peer_name} => {peer_group_name} => {target_name}"'
                    )
                    continue
                if target_port:
                    for port in target_port:
                        post_up.append(
                            f'iptables --append FORWARD --source {peer_ip_address} --dest {target_ip_address} -p tcp --dport {port} -j ACCEPT -m comment --comment "{peer_name} => {peer_group_name} => {target_name}"'
                        )
                else:
                    post_up.append(
                        f'iptables --append FORWARD --source {peer_ip_address} --dest {target_ip_address} -j ACCEPT -m comment --comment "{peer_name} => {peer_group_name} => {target_name}"'
                    )

        # add FORWARD and ACCEPT rules for each chain - networks only but NOT INTERNET!
        for (
            chain_name,
            target_name,
            target_disabled,
            target_is_network_address,
            target_ip_address,
            target_network_address,
            target_port,
            peer_group_name,
            peer_group_disabled,
            peer_infos,
        ) in target_infos:
            if not target_is_network_address:
                continue
            if target_network_address == internet__network_address:
                continue
            for peer_name, peer_disabled, peer_ip_address in peer_infos:
                if peer_disabled:
                    post_up.append(
                        f'iptables --append FORWARD --source {peer_ip_address} -j DROP -m comment --comment "{peer_name} => {peer_group_name} => {target_name}"',
                    )
                    continue
                post_up.append(
                    f'iptables --append FORWARD --source {peer_ip_address} --dest {target_network_address} -j ACCEPT -m comment --comment "{peer_name} => {peer_group_name} => {target_name}"'
                )

        local_networks = []
        if serverConfiguration.local_networks:
            local_networks = [
                x for x in serverConfiguration.local_networks.split(",") if x
            ]
        targets_to_block = local_networks  # + [str(vpn_network_address)]
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
            target_port,
            peer_group_name,
            peer_group_disabled,
            peer_infos,
        ) in target_infos:
            if not target_is_network_address:
                continue
            if target_network_address != internet__network_address:
                continue
            for peer_name, peer_disabled, peer_ip_address in peer_infos:
                if peer_disabled:
                    post_up.append(
                        f'iptables --append FORWARD --source {peer_ip_address} -j DROP -m comment --comment "{peer_name} => {peer_group_name} => {target_name}"'
                    )
                    continue
                post_up.append(
                    f'iptables --append FORWARD --source {peer_ip_address} --dest {target_network_address} -j ACCEPT -m comment --comment "{peer_name} => {peer_group_name} => {target_name}"'
                )

        post_up.append(
            'iptables -A FORWARD -j DROP -m comment --comment "DROP - everything else"'
        )

        post_up += ["\n", "iptables -n -L -v --line-numbers;", "\n"]

        post_up = "\n".join(post_up)

        post_down = [
            "iptables --flush",
            "iptables --table nat --flush",
            "iptables --delete-chain",
            "",
            "iptables -n -L -v --line-numbers",
        ]

        post_down = "\n".join(post_down)

        return (post_up, post_down)

    @logged
    def generate_configuration_files(
        self, serverConfiguration, targets, peer_groups, peers
    ):
        # first save wg0.conf
        ensure_folder_exists_for_file(serverConfiguration.wireguard_config_path)
        configs = self.get_wireguard_configuration(
            serverConfiguration=serverConfiguration,
            peer_groups=peer_groups,
            peers=peers,
        )
        with open(serverConfiguration.wireguard_config_path, "w") as f:
            server_config = configs["server_configuration"]
            f.write(f"{server_config}\n")

        # save post-up/post-down scripts
        ensure_folder_exists_for_file(serverConfiguration.script_path_post_up)
        ensure_folder_exists_for_file(serverConfiguration.script_path_post_down)
        iptables_scripts_post_up, iptables_scripts_post_down = (
            self.get_wireguard_iptables_script(
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
        command = f"sudo wg-quick down {sc.wireguard_config_path};sudo conntrack -F; sudo conntrack -F; sudo conntrack -F; sudo wg-quick up {sc.wireguard_config_path};"
        output = self.execute_process(command)
        res = {"status": "ok", "output": output}
        return res

    @logged
    def get_connected_peers(self, peers, serverConfiguration):
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
        res["message"] = ""
        res["datetime"] = dt.strftime("%Y-%m-%d %H:%M:%S")
        res["items"] = []
        for match_num, match in enumerate(matches, start=1):
            peer_item = {}
            peer_item["peer_name"] = f"unknown-{match_num}"
            peer_item["end_point"] = None
            peer_item["latest_handshake"] = None
            peer_item["transfer_rx"] = None
            peer_item["transfer_tx"] = None
            peer_item["status"] = None
            peer_item["ping_time_ms"] = None

            peer_data = match.groupdict()

            peer_item["allowed_ips_ip"] = peer_data["allowed_ips_ip"]

            peers_filtered = [
                x for x in peers if x.public_key == peer_data["public_key"]
            ]
            peer = peers_filtered[0] if peers_filtered else None
            if peer:
                is_inactive = False
                is_connected = False
                last_handshake = None
                is_disabled = peer.disabled
                peer_item["peer_name"] = peer.name
                peer_item["status"] = "Disabled" if is_disabled else peer_item["status"]
                if not is_disabled:
                    is_connected = (
                        True
                        if "end_point_ip" in peer_data.keys()
                        and peer_data["end_point_ip"]
                        else False
                    )
                    if is_connected and ("latest_handshake" in peer_data.keys()):
                        last_handshake = datetime.datetime.fromtimestamp(
                            int(peer_data["latest_handshake"])
                        ).astimezone(tz=dt.tzinfo)
                        timediff = dt - last_handshake
                        is_inactive = (
                            timediff.total_seconds() >= MAX_LAST_HANDSHAKE_SECONDS
                        )
                    if is_connected:
                        peer_item["latest_handshake"] = (
                            last_handshake.strftime("%Y-%m-%d %H:%M:%S")
                            if last_handshake
                            else None
                        )
                        peer_item["end_point_ip"] = peer_data["end_point_ip"]
                        if "transfer_rx" in peer_data.keys():
                            peer_item["transfer_rx"] = int(peer_data["transfer_rx"])
                        if "transfer_tx" in peer_data.keys():
                            peer_item["transfer_tx"] = int(peer_data["transfer_tx"])
                    peer_item["status"] = (
                        "Inactive"
                        if is_inactive
                        else "Connected" if is_connected else peer_item["status"]
                    )
                peer_item["is_connected"] = is_connected
                peer_item["is_inactive"] = is_inactive
            res["items"] += [peer_item]
        return res

    @logged
    def get_iptables_log(self):
        command = "sudo iptables -n -L -v --line-numbers;sudo iptables -t nat -n -L -v --line-numbers;"
        output = self.execute_process(command)
        dt = datetime.datetime.now().astimezone()
        res = {}
        res["status"] = "ok"
        res["datetime"] = dt.strftime("%Y-%m-%d %H:%M:%S")
        res["output"] = output
        return res

    @logged
    def get_server_status(self, last_db_change_datetime, wireguard_config_change_datetime):
        res = {}
        res["status"] = "ok"
        res["hostname"] = socket.gethostname()
        res["platform"] = platform.platform()
        res["platform_version"] = platform.version()
        res["platform_system"] = platform.system()
        res["platform_processor"] = platform.processor()
        res["platform_architecture"] = platform.machine()
        res["need_regenerate_files"] = False
        files = glob.glob("/config/wireguard/**/*", recursive=True)
        last_file_change_timestamps = [os.path.getmtime(x) for x in files]
        last_file_change_timestamp = (
            max(last_file_change_timestamps) if last_file_change_timestamps else 0
        )

        wireguard_config_file_datetime = datetime.datetime.fromtimestamp(
            last_file_change_timestamp, timezone.get_current_timezone()
        )

        res["last_db_change_datetime"] = last_db_change_datetime
        res["wireguard_config_file_datetime"] = wireguard_config_file_datetime
        res["wireguard_config_change_datetime"] = wireguard_config_change_datetime

        if (wireguard_config_change_datetime is None) or (
            wireguard_config_change_datetime > wireguard_config_file_datetime
        ):
            res["need_regenerate_files"] = True
            res["message"] = "Configuration files need to be regenerated."
            res["status"] = "warning"

        return res
