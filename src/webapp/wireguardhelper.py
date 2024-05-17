#!/usr/bin/python
import os
import ipaddress
from functools import wraps
from dataclasses import dataclass
import random
from flask import Flask, send_from_directory, send_file
from flask import request
from flask import jsonify
import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import Integer
from sqlalchemy import inspect
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import joinedload, defaultload
from sqlalchemy import select
from typing import List
import docker
import pathlib
import codecs
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives import serialization
import qrcode
from io import BytesIO
import subprocess
import re

from common import *
from utils import *
from models import *
from dbhelper import DbHelper


class WireGuardHelper(object):
    def __init__(self, dbRepo):
        self.dbRepo = dbRepo

    @logged
    def getWireguardConfigurationForServer(self, serverConfiguration):
        server_config = [
            f'# Settings for this peer.',
            f'[Interface]',
            f'Address = {serverConfiguration.ip_address}',
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

        peer_config_client_side = [
            f'# Settings for this peer.',
            f'[Interface]',
            f'Address = {peer.ip_address}',
            f'ListenPort = {peer.port}',
            f'PrivateKey = {peer.private_key}',
            f'DNS = 192.168.0.5',
            #f'DNS = {serverConfiguration.ip_address}',
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
    def getWireguardConfiguration(self):
        
        serverConfiguration = self.dbRepo.getServerConfiguration(1)
        server_config = self.getWireguardConfigurationForServer(serverConfiguration)

        # now generate configs for peers
        # both for the server side and client side
        peer_configs = []
        peers = self.dbRepo.getPeers()
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
    def getWireguardIpTablesScript(self):
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

        targets = self.dbRepo.getTargetsForIPTablesRules()
        peers = self.dbRepo.getPeers()

        chain_name_local_domains = 'chain-local-domains'

        post_up += [f'# create chains for targets',]
        rules = [
            f'iptables -N {chain_name_local_domains}',
        ]
        post_up += rules
        for target in targets:
            if not target.peer_group_target_links:
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
            for pg_target_link in target.peer_group_target_links:
                for pg_peer_link in pg_target_link.peer_group.peer_group_peer_links:
                    chain_name = self.get_chain_name(target)
                    comment = f'FWD - {pg_peer_link.peer.name} => {pg_target_link.peer_group.name} => {target.name}'
                    rules = [
                        f'# {comment}',
                        f'iptables --append FORWARD --source {pg_peer_link.peer.ip_address} --destination {target_ip_address} -j {chain_name} -m comment --comment "{comment}"',
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
            for pg_target_link in target.peer_group_target_links:
                for pg_peer_link in pg_target_link.peer_group.peer_group_peer_links:
                    chain_name = self.get_chain_name(target)
                    comment = f'FWD - {pg_peer_link.peer.name} => {pg_target_link.peer_group.name} => {target.name}'
                    rules = [
                        f'# {comment}',
                        f'iptables --append FORWARD --source {pg_peer_link.peer.ip_address} --destination {target_network_address} -j {chain_name} -m comment --comment "{comment}"',
                        f'',
                    ]
                    post_up += rules

        serverConfiguration = self.dbRepo.getServerConfiguration(1)
        for peer in peers:
            local_domains = ['192.168.0.0/24']
            server_ip_address = ipaddress.ip_interface(serverConfiguration.ip_address)
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
            for pg_target_link in target.peer_group_target_links:
                for pg_peer_link in pg_target_link.peer_group.peer_group_peer_links:
                    chain_name = self.get_chain_name(target)
                    comment = f'FWD - {pg_peer_link.peer.name} => {pg_target_link.peer_group.name} => {target.name}'
                    rules = [
                        f'# {comment}',
                        f'iptables --append FORWARD --source {pg_peer_link.peer.ip_address} --destination {target_network_address} -j {chain_name} -m comment --comment "{comment}"',
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
            for pg_target_link in target.peer_group_target_links:
                for pg_peer_link in pg_target_link.peer_group.peer_group_peer_links:
                    chain_name = self.get_chain_name(target)
                    comment = f'ACCEPT - {pg_peer_link.peer.name} => {pg_target_link.peer_group.name} => {target.name}({target_ip_address})'
                    rules = [
                        f'# {comment}',
                        f'iptables --append {chain_name} --source {pg_peer_link.peer.ip_address} --destination {target_network_address} -j ACCEPT  -m comment --comment "{comment}"',
                        f'',
                    ]
                    post_up += rules

        rules = [
            f'# now add DROP rule to all user-defined chains',
        ]
        post_up += rules

        for target in targets:
            if not target.peer_group_target_links:
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
    def generateConfigurationFiles(self):
        serverConfiguration = self.dbRepo.getServerConfiguration(1)
        
        # first save wg0.conf
        ensure_folder_exists_for_file(serverConfiguration.wireguard_config_path)
        configs = self.getWireguardConfiguration();
        with open(serverConfiguration.wireguard_config_path, 'w') as f:
            server_config = configs['server_configuration']
            f.write(f"{server_config}\n")

        # save post-up/post-down scripts        
        ensure_folder_exists_for_file(serverConfiguration.script_path_post_up)
        ensure_folder_exists_for_file(serverConfiguration.script_path_post_down)
        iptables_scripts_post_up, iptables_scripts_post_down = self.getWireguardIpTablesScript();
        with open(serverConfiguration.script_path_post_up, 'w') as f:
            f.write(f"{iptables_scripts_post_up}\n")
        with open(serverConfiguration.script_path_post_down, 'w') as f:
            f.write(f"{iptables_scripts_post_down}\n")
