#!/usr/bin/python
import os
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

IP_ADDRESS_INTERNET = '0.0.0.0/0'

logger = logging.getLogger(__name__)

def logged(func):
    @wraps(func)
    def logger_func(*args, **kwargs):
        func_name = func.__name__
        try:
            logger.debug(f'{func_name}: start')
            res = func(*args, **kwargs)
            return res
        finally:
            logger.debug(f'{func_name}: end')

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
        logger.warning(f'Directory was missing. Created: {dir}')

def generate_keys():
    # generate private key
    private_key = X25519PrivateKey.generate()
    private_bytes = private_key.private_bytes( encoding = serialization.Encoding.Raw, format = serialization.PrivateFormat.Raw, encryption_algorithm = serialization.NoEncryption())
    key_private = codecs.encode(private_bytes, 'base64').decode('utf8').strip()

    # derive public key
    public_bytes = private_key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    key_public = codecs.encode(public_bytes, 'base64').decode('utf8').strip()
    return (key_public, key_private)

class WireGuardHelper(object):
    @logged
    def getWireguardConfigurationForServer(self, serverConfiguration):
        server_config = [
            f'# Settings for this peer.',
            f'[Interface]',
            f'Address = {serverConfiguration.network_address}',
            f'ListenPort = {serverConfiguration.port_internal}',
            f'PrivateKey = {serverConfiguration.private_key}',
            f'',
            f'PostUp = {serverConfiguration.script_path_post_up}',
            f'PostDown = {serverConfiguration.script_path_post_down}',
            f'',
            f'',
            f'',
        ]
        res = '\n'.join(server_config)
        return res

    @logged
    def getWireguardConfigurationsForPeer(self, serverConfiguration, peer):
        # returns tuple of server-side and client-side configurations
        peer_config_server_side = [
            f'# Settings for the peer on the other side of the pipe.',
            f'# {peer.name}: disabled',
            f'',
            ] if peer.disabled else [
            f'# Settings for the peer on the other side of the pipe.',
            f'# {peer.name}',
            f'[Peer]',
            f'PublicKey = {peer.public_key}',
            #f'#PresharedKey = <this is optional>',
            f'AllowedIPs = {peer.ip_address}/32',
            f'PersistentKeepalive = 25',
            f'',
            f'',
        ]
        peer_config_server_side = '\n'.join(peer_config_server_side)

        peer_port = peer.port if peer.port else serverConfiguration.peer_default_port

        peer_config_client_side = [
            f'# Settings for the peer on the other side of the pipe.',
            f'# {peer.name}: disabled',
            f'',
            ] if peer.disabled else [
            f'# Settings for this peer.',
            f'[Interface]',
            f'Address = {peer.ip_address}',
            f'ListenPort = {peer_port}',
            f'PrivateKey = {peer.private_key}',
            f'DNS = 192.168.0.5',
            #f'DNS = {serverConfiguration.network_address}',
            f'',
            f'',
            f'# Settings for the peer on the other side of the pipe.',
            f'[Peer]',
            f'PublicKey = {serverConfiguration.public_key}',
            f'Endpoint = {serverConfiguration.host_name_external}:{serverConfiguration.port_external}',
            f'AllowedIPs = 0.0.0.0/0',
        ]
        peer_config_client_side = '\n'.join(peer_config_client_side)
        res = (peer_config_server_side, peer_config_client_side)
        return res

    @logged
    def getWireguardConfiguration(self, serverConfiguration, peers):
       
        server_config = self.getWireguardConfigurationForServer(serverConfiguration)

        # now generate configs for peers
        # both for the server side and client side
        peer_configs = []
        for peer in peers:
            peer_config_server_side, peer_config_client_side = self.getWireguardConfigurationsForPeer(serverConfiguration, peer)
            server_config += peer_config_server_side
            peer_configs += [peer_config_client_side]

        res = {}
        res['server_configuration'] = server_config
        res['peer_configurations'] = peer_configs
        return res
    
    def get_chain_name(self, target):
        res = 'chain-' + re.sub(r'[^a-zA-Z0-9]', '', str(target.name))
        return res
    
    @logged
    def getWireguardIpTablesScript(self, serverConfiguration, targets, peers):
        dns_servers = ["192.168.0.5",]
        # generate post-up script
        post_up = [
            f'#!/bin/bash',
            f'WIREGUARD_INTERFACE=wg0',
            f'WIREGUARD_LAN=192.168.2.0/24',
            f'LAN_INTERFACE=eth0',
            f'LOCAL_LAN=192.168.0.0/24',

            f'echo "***** PostUp: Configuration ******************** "',
            f'echo "WIREGUARD_LAN: ${{WIREGUARD_LAN}}"',
            f'echo "LAN_INTERFACE: ${{LAN_INTERFACE}}"',
            f'echo "LOCAL_LAN    : ${{LOCAL_LAN}}"',
            f'echo "************************************************ "',
            f'',
            f'# clear existing rules and setup defaults',
            f'iptables --flush',
            f'iptables --table nat --flush',
            f'iptables --delete-chain',
            f'',
            f'',
            f'# masquerade traffic related to wg0',
            f'iptables -t nat -I POSTROUTING -o ${{LAN_INTERFACE}} -j MASQUERADE -s $WIREGUARD_LAN',
            f'',
            f'# Accept related or established traffic',
            f'iptables -A FORWARD -m state --state RELATED,ESTABLISHED -j ACCEPT -m comment --comment "Established and related packets."',
            f'',
        ]

        for dns_server in dns_servers:
            rules = [
                f'# now make all DNS traffic flow to desired DNS server',
                f'iptables -t nat -I PREROUTING -p udp --dport 53 -j DNAT --to {dns_server}:53',
                f'',
                ]
            post_up += rules

        chain_name_local_domains = 'chain-local-domains'

        post_up += [f'# create chains for targets',]
        rules = [
            f'iptables -N {chain_name_local_domains}',
        ]
        post_up += rules
        for target in targets:
            if not target.peer_groups:
                # if there are no links with Peer-Groups, do not create the chain
                continue
            chain_name = self.get_chain_name(target)
            rules = [
                f'iptables -N {chain_name}',
            ]
            post_up += rules

        post_up += [
                f'iptables --append FORWARD -p udp -m udp --dport 53 -j ACCEPT -m comment --comment "ALLOW - All DNS traffic"',
                f'iptables --append {chain_name_local_domains} -j DROP -m comment --comment "DROP - Everything for local domains"',
            ]

        # per target FORWARD - host
        for target in targets:
            target_is_network_address, target_ip_address, target_network_address = is_network_address(target.ip_address)
            if target_is_network_address:
                continue
            for peer_group in target.peer_groups:
                peer_group_peers = peers if peer_group.name == 'EveryOne' else peer_group.peers.all()
                for peer in peer_group_peers:
                    chain_name = self.get_chain_name(target)
                    comment = f'FWD - {peer.name} => {peer_group.name} => {target.name}'
                    rules = [
                        f'# {comment}',
                        f'iptables --append FORWARD --source {peer.ip_address} --destination {target_ip_address} -j {chain_name} -m comment --comment "{comment}"',
                        f'',
                    ]
                    post_up += rules

        # per target FORWARD - network - non-Internet only
        for target in targets:
            target_is_network_address, target_ip_address, target_network_address = is_network_address(target.ip_address)
            if not target_is_network_address:
                continue
            if str(target_network_address) == IP_ADDRESS_INTERNET:
                continue
            for peer_group in target.peer_groups.all():
                peer_group_peers = peers if peer_group.name == 'EveryOne' else peer_group.peers.all()
                for peer in peer_group_peers:
                    chain_name = self.get_chain_name(target)
                    comment = f'FWD - {peer.name} => {peer_group.name} => {target.name}'
                    rules = [
                        f'# {comment}',
                        f'iptables --append FORWARD --source {peer.ip_address} --destination {target_network_address} -j {chain_name} -m comment --comment "{comment}"',
                        f'',
                    ]
                    post_up += rules

        for peer in peers:
            local_domains = ['192.168.0.0/24']
            server_ip_address = ipaddress.ip_interface(serverConfiguration.network_address)
            targets_to_block = [
                str(server_ip_address.network),
            ] + local_domains
            comment = f'DROP - Everything else on LAN for {peer.name}'
            rules = [
                f'iptables --append FORWARD --source {peer.ip_address} --destination {target} -j {chain_name_local_domains} -m comment --comment "{comment} - {target}"' for target in targets_to_block
                ]
            post_up += rules

        # per target FORWARD - network - Internet only
        for target in targets:
            target_is_network_address, target_ip_address, target_network_address = is_network_address(target.ip_address)
            if not target_is_network_address:
                continue
            if str(target_network_address) != IP_ADDRESS_INTERNET:
                continue
            if not target.peer_groups:
                continue
            for peer_group in target.peer_groups.all():
                peer_group_peers = peers if peer_group.name == 'EveryOne' else peer_group.peers.all()
                for peer in peer_group_peers:
                    chain_name = self.get_chain_name(target)
                    comment = f'FWD - {peer.name} => {peer_group.name} => {target.name}'
                    rules = [
                        f'# {comment}',
                        f'iptables --append FORWARD --source {peer.ip_address} --destination {target_network_address} -j {chain_name} -m comment --comment "{comment}"',
                        f'',
                    ]
                    post_up += rules

        rules = [
            f'iptables -A FORWARD -j DROP -m comment --comment "DROP - everything else"',
        ]
        post_up += rules

        # per peer rules now for host addresses only
        for target in targets:
            target_is_network_address, target_ip_address, target_network_address = is_network_address(target.ip_address)
            if target_is_network_address:
                continue
            for pg_target_link in target.peer_group_target_links:
                for pg_peer_link in pg_target_link.peer_group.peer_group_peer_links:
                    chain_name = self.get_chain_name(target)
                    comment = f'ACCEPT - {pg_peer_link.peer.name} => {pg_target_link.peer_group.name} => {target.name}({target_ip_address})'
                    rules = [
                        f'# {comment}',
                        f'iptables --append {chain_name} --source {pg_peer_link.peer.ip_address} --destination {target_ip_address} -j ACCEPT  -m comment --comment "{comment}"',
                        f'',
                    ]
                    post_up += rules

        # per peer rules now for network addresses only
        for target in targets:
            target_is_network_address, target_ip_address, target_network_address = is_network_address(target.ip_address)
            if not target_is_network_address:
                continue
            for peer_group in target.peer_groups.all():
                peer_group_peers = peers if peer_group.name == 'EveryOne' else peer_group.peers.all()
                for peer in peer_group_peers:
                    chain_name = self.get_chain_name(target)
                    comment = f'ACCEPT - {peer.name} => {peer_group.name} => {target.name}({target_ip_address})'
                    rules = [
                        f'# {comment}',
                        f'iptables --append {chain_name} --source {peer.ip_address} --destination {target_network_address} -j ACCEPT  -m comment --comment "{comment}"',
                        f'',
                    ]
                    post_up += rules

        rules = [
            f'# now add DROP rule to all user-defined chains',
        ]
        post_up += rules

        for target in targets:
            if not target.peer_groups:
                # if there are no links with Peer-Groups, do not create the chain
                continue
            chain_name = self.get_chain_name(target)
            rules = [
                f'iptables -A {chain_name} -j DROP -m comment --comment "DROP - everything else"',
            ]
            post_up += rules

        post_up += ['\n' , 'iptables -n -L -v --line-numbers;' , '\n']

        post_up = '\n'.join(post_up)

        post_down = [
            f'iptables --flush',
            f'iptables --table nat --flush',
            f'iptables --delete-chain',
            f'',
            f'iptables -n -L -v --line-numbers',
        ]

        post_down = '\n'.join(post_down)

        return (post_up, post_down)
    
    @logged
    def generateConfigurationFiles(self, serverConfiguration, targets, peers):
        
        # first save wg0.conf
        ensure_folder_exists_for_file(serverConfiguration.wireguard_config_path)
        configs = self.getWireguardConfiguration(serverConfiguration=serverConfiguration, peers=peers);
        with open(serverConfiguration.wireguard_config_path, 'w') as f:
            server_config = configs['server_configuration']
            f.write(f"{server_config}\n")

        # save post-up/post-down scripts        
        ensure_folder_exists_for_file(serverConfiguration.script_path_post_up)
        ensure_folder_exists_for_file(serverConfiguration.script_path_post_down)
        iptables_scripts_post_up, iptables_scripts_post_down = self.getWireguardIpTablesScript(serverConfiguration=serverConfiguration, targets = targets, peers = peers);
        with open(serverConfiguration.script_path_post_up, 'w') as f:
            f.write(f"{iptables_scripts_post_up}\n")
        with open(serverConfiguration.script_path_post_down, 'w') as f:
            f.write(f"{iptables_scripts_post_down}\n")
        output1 = self.execute_process(f'sudo chmod +x {serverConfiguration.script_path_post_up}')
        output2 = self.execute_process(f'sudo chmod +x {serverConfiguration.script_path_post_down}')
        res = {'status': 'ok', 'output': output1 + '\n' + output2 }
        return res

    @logged
    def execute_process(Self, command):
        output = ''
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        try:
            outs, errs = proc.communicate(timeout = 60)
            output = outs.decode('utf-8') + errs.decode('utf-8')
        except subprocess.TimeoutExpired:
            proc.kill()
        res = output
        logger.debug(output)
        return res
    
    @logged
    def restart(self, serverConfiguration):
        sc = serverConfiguration
        command = f'sudo wg-quick down {sc.wireguard_config_path}; sudo wg-quick up {sc.wireguard_config_path}; sudo conntrack -F; sudo conntrack -F; sudo conntrack -F;'
        output = self.execute_process(command)
        res = {'status': 'ok', 'output': output }
        return res