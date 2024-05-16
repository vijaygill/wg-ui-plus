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

class DbHelper(object):
    def __init__(self):
        self.db_file = os.path.abspath(DB_FILE)
        needs_data_seeding = not os.path.exists(self.db_file)

        self.createDatabase()

        if needs_data_seeding:
            self.createDictionaryData()
            self.createSampleData()

    @logged
    def createDatabase(self):
        ensure_folder_exists_for_file(self.db_file)
        self.engine = create_engine(f'sqlite:///{DB_FILE}', echo = True)
        Base.metadata.create_all(self.engine)

    @logged
    def createDictionaryData(self):
        self.createDictionaryDataTargets()
        self.createDictionaryDataPeerGroups()
        self.createDictionaryDataServerConfiguration()

    @logged
    def createDictionaryDataServerConfiguration(self):
        with Session(self.engine) as session:
            existing_rows = [ r.name for r in session.query( ServerConfiguration ).all() ]
            rows_to_create = [ x for x in DICT_DATA_SERVER_CONFIGURATION if x[0] not in existing_rows]
            for r in rows_to_create:
                host_name_external, ip_address, port_internal, port_external, wireguard_config_path, script_path_post_up, script_path_post_down = r
                public_key, private_key = generate_keys()
                new_row = ServerConfiguration(ip_address = ip_address,
                                              host_name_external = host_name_external,
                                              port_internal = port_internal,
                                              port_external = port_external,
                                              wireguard_config_path = wireguard_config_path,
                                              script_path_post_up = script_path_post_up, 
                                              script_path_post_down = script_path_post_down, 
                                              public_key = public_key, private_key = private_key,
                                              peer_default_port = PORT_DEFAULT_EXTERNAL )
                session.add(new_row)
                session.commit()
        pass

    @logged
    def createDictionaryDataPeerGroups(self):
        with Session(self.engine) as session:
            existing_rows = [ r.name for r in session.query( PeerGroup ).all() ]
            rows_to_create = [ x for x in DICT_DATA_PEER_GROUPS if x[0] not in existing_rows]

            for r in rows_to_create:
                name, description, allow_modify_peers, allow_modify_targets = r
                new_row = PeerGroup( name = name, description = description, allow_modify_self = True, allow_modify_peers = allow_modify_peers, allow_modify_targets = allow_modify_targets )
                if name == DICT_DATA_PEER_GROUP_EVERYONE:
                    # if PeerGroup is everyone, link Internet by default
                    stmt = select(Target).where(Target.name == DICT_DATA_TARGET_INTERNET)
                    target_internet = list(session.scalars(stmt).unique().all())[0]
                    new_row.peer_group_target_links = [PeerGroupTargetLink(target = target_internet, target_id = target_internet.id, peer_group = new_row)]
                session.add(new_row)
                session.commit()

    @logged
    def createDictionaryDataTargets(self):
        with Session(self.engine) as session:
            existing_rows = [ r.name for r in session.query( Target ).all() ]
            rows_to_create = [ x for x in DICT_DATA_TARGETS if x[0] not in existing_rows]

            for r in rows_to_create:
                name, description, ip_address = r
                new_row = Target( name = name, description = description, ip_address = ip_address, allow_modify_self = False, allow_modify_peer_groups = True )
                session.add(new_row)
                session.commit()
				
    @logged
    def createSampleData(self):
        with Session(self.engine) as session:
            existing_rows = [ r.name for r in session.query( Target ).all() ]
            rows_to_create = [ x for x in SAMPLE_DATA_TARGETS if x[0] not in existing_rows]

            for r in rows_to_create:
                name, description, ip_address = r
                new_row = Target( name = name, description = description, ip_address = ip_address )
                session.add(new_row)
                session.commit()

        with Session(self.engine) as session:
            existing_rows = [ r.name for r in session.query( PeerGroup ).all() ]
            rows_to_create = [ x for x in SAMPLE_DATA_PEER_GROUPS if x[0] not in existing_rows]

            for r in rows_to_create:
                name, description, allow_modify_peers, allow_modify_targets = r
                new_row = PeerGroup( name = name, description = description, allow_modify_peers = allow_modify_peers, allow_modify_targets = allow_modify_targets)
                session.add(new_row)
                session.commit()


        peers = self.getPeers()
        if not peers:
            with Session(self.engine) as session:
                SAMPLE_MAX_PEERS = 5
                
                serverConfiguration = self.getServerConfiguration(1)
                server_ip_address = ipaddress.ip_interface(serverConfiguration.ip_address)
                for i in range(0, SAMPLE_MAX_PEERS):
                    ip_address = server_ip_address.ip + 10 + i
                    public_key, private_key = generate_keys()
                    peer = Peer(name = f'Peer - {i}',
                                ip_address = str(ip_address), port = serverConfiguration.peer_default_port,
                                public_key = public_key, private_key = private_key)
                    session.add(peer)
                    session.commit()
                peer_groups = [x for x in session.query( PeerGroup ).all()]
                peers = [x for x in session.query( Peer ).all()]
                for peer in peers:
                    pgp_link = PeerGroupPeerLink(peer = peer, peer_group = peer_groups[0])
                    session.add(pgp_link)
                    session.commit()
                    rnd = random.randrange(1, 100)
                    if rnd > 50:
                        pgp_link = PeerGroupPeerLink(peer = peer, peer_group = peer_groups[2])
                        session.add(pgp_link)
                        session.commit()
                

    @logged
    def getPeers(self, for_api = False):
        with Session(self.engine) as session:
            stmt = select(Peer)
            res = session.scalars(stmt).unique().all()
            res = [row2dict(x) for x in res] if for_api else res
            return res
    
    @logged
    def getPeer(self, id, for_api = False):
        with Session(self.engine) as session:
            stmt = select(Peer).options(joinedload(Peer.peer_group_peer_links)
                                        .joinedload(PeerGroupPeerLink.peer_group)).where(Peer.id == id)
            peers = list(session.scalars(stmt).unique().all())
            peer = peers[0] if peers else Peer()
            res = row2dict(peer) if for_api else peer
            if for_api:
                # add peer-groups also for lookup but which are not already added
                lookup_peer_groups = self.getPeerGroups()
                lookup_peer_groups = [x for x in lookup_peer_groups if x.id not in [link.peer_group.id for link in peer.peer_group_peer_links]]
                lookup_peer_groups = [PeerGroupPeerLink(peer_group_id = x.id, peer_group = x) for x in lookup_peer_groups]
                lookup_peer_groups = [row2dict(x) for x in lookup_peer_groups]
                res['lookup_peer_groups'] = lookup_peer_groups
                if (not 'peer_group_peer_links' in res.keys()) or (not res['peer_group_peer_links']):
                    res['peer_group_peer_links'] = []
            return res

    @logged
    def validate_peer(self, peerToSave, for_api = False):
        errors = []
        peer = dict2row(Peer, peerToSave, True)
        if (not peer.name) or (len(peer.name.strip()) <= 0):
            errors.append({'field': 'name', 'type': 'error','message': 'Name is not provided or is blank.'})
        if (not peer.peer_group_peer_links) or (len(peer.peer_group_peer_links) <= 0):
            errors.append({'field': 'peer_group_peer_links', 'type': 'warning', 'message': 'No Peer-Groups added.'})
        return errors

    @logged
    def savePeer(self, peerToSave, for_api = False):
        with Session(self.engine) as session:
            peer = dict2row(Peer, peerToSave, True)
            sc = self.getServerConfiguration(1)
            if peer.ip_address is None:
                ip_address = ''
                peers = self.getPeers()
                if peers:
                    ip_address_num_max = max([ int(ipaddress.ip_interface(p.ip_address).ip) for p in self.getPeers()] )
                    ip_address = ip_address_num_max + 1
                else:
                    ip_address = int(ipaddress.ip_interface(sc.ip_address).ip) + 1
                peer.ip_address = str(ipaddress.ip_address(ip_address))
            
            if not peer.port:
                peer.port = sc.peer_default_port

            peer = session.merge(peer)
            session.commit()
            res = row2dict(peer) if for_api else peer
            return res

    @logged
    def getPeerGroups(self, for_api = False):
        with Session(self.engine) as session:
            stmt = select(PeerGroup)
            res = session.scalars(stmt).unique().all()
            if(for_api):
                res = [row2dict(x) for x in res]
            return res

    @logged
    def getPeerGroup(self, id, for_api = False):
        with Session(self.engine) as session:
            opts1 = joinedload(PeerGroup.peer_group_peer_links).options(joinedload(PeerGroupPeerLink.peer))
            opts2 = joinedload(PeerGroup.peer_group_target_links).options(joinedload(PeerGroupTargetLink.target))
            stmt = select(PeerGroup).options(opts1, opts2).where(PeerGroup.id == id)
            peerGroups = list(session.scalars(stmt).unique().all())
            peerGroup = peerGroups[0] if peerGroups else PeerGroup(allow_modify_self = True,allow_modify_peers = True,allow_modify_targets = True)
            res = row2dict(peerGroup) if for_api else peerGroup
            if for_api:
                # add peers also for lookup but which are not already added
                lookup_peers = self.getPeers()
                lookup_peers = [x for x in lookup_peers if x.id not in [link.peer.id for link in peerGroup.peer_group_peer_links]]
                lookup_peers = [PeerGroupPeerLink(peer_id = x.id, peer = x) for x in lookup_peers]
                lookup_peers = [row2dict(x) for x in lookup_peers]
                res['lookup_peers'] = lookup_peers
                # add targets also for lookup but which are not already added
                lookup_targets = self.getTargets()
                lookup_targets = [x for x in lookup_targets if x.id not in [link.target.id for link in peerGroup.peer_group_target_links]]
                lookup_targets = [PeerGroupTargetLink(target_id = x.id, target = x) for x in lookup_targets]
                lookup_targets = [row2dict(x) for x in lookup_targets]
                res['lookup_targets'] = lookup_targets
                if (not 'peer_group_peer_links' in res.keys()) or (not res['peer_group_peer_links']):
                    res['peer_group_peer_links'] = []
                if (not 'peer_group_target_links' in res.keys()) or (not res['peer_group_target_links']):
                    res['peer_group_target_links'] = []
            return res

    @logged
    def validate_peer_group(self, peerGroupToSave, for_api = False):
        errors = []
        peer_group = dict2row(PeerGroup, peerGroupToSave, True)
        if (not peer_group.name) or (len(peer_group.name.strip()) <= 0):
            errors.append({'field': 'name', 'type': 'error','message': 'Name is not provided or is blank.'})
        if (not peer_group.description) or (len(peer_group.description.strip()) <= 0):
            errors.append({'field': 'description', 'type': 'error', 'message': 'Description is not provided or is blank.'})
        if (not peer_group.peer_group_peer_links) or (len(peer_group.peer_group_peer_links) <= 0):
            errors.append({'field': 'peers', 'type': 'warning', 'message': 'No peers added.'})
        if (not peer_group.peer_group_target_links) or (len(peer_group.peer_group_target_links) <= 0):
            errors.append({'field': 'targets', 'type': 'warning', 'message': 'No targets added.'})
        return errors

    @logged
    def savePeerGroup(self, peerGroupToSave, for_api = False):
        with Session(self.engine) as session:
            peerGroup = dict2row(PeerGroup, peerGroupToSave, True)
            peerGroup.allow_modify_self = DICT_DATA_PEER_GROUP_EVERYONE != peerGroup.name
            peerGroup.allow_modify_peers = DICT_DATA_PEER_GROUP_EVERYONE != peerGroup.name
            peerGroup.allow_modify_targets = True
            peerGroup = session.merge(peerGroup)
            session.commit()
            res = row2dict(peerGroup) if for_api else peerGroup
            return res

    @logged
    def getTargets(self, for_api = False):
        with Session(self.engine) as session:
            stmt = select(Target)
            res = session.scalars(stmt).unique().all()
            res = [row2dict(x) for x in res] if for_api else res
            return res
    
    @logged
    def getTarget(self, id, for_api = False):
        with Session(self.engine) as session:
            opts = joinedload(Target.peer_group_target_links).options(joinedload(PeerGroupTargetLink.peer_group))
            stmt = select(Target).options(opts).where(Target.id == id)
            targets = list(session.scalars(stmt).unique().all())
            target = targets[0] if targets else Target()
            if target.allow_modify_self is None:
                target.allow_modify_self = True
            target.allow_modify_peer_groups = True
            res = row2dict(target) if for_api else target
            if for_api:
                # add peers also for lookup but which are not already added
                lookup_peergroups = self.getPeerGroups()
                lookup_peergroups = [x for x in lookup_peergroups if x.id not in [link.peer_group.id for link in target.peer_group_target_links]]
                lookup_peergroups = [PeerGroupTargetLink(peer_group_id = x.id, peer_group = x) for x in lookup_peergroups]
                lookup_peergroups = [row2dict(x) for x in lookup_peergroups]
                res['lookup_peergroups'] = lookup_peergroups
                if (not 'peer_group_target_links' in res.keys()) or (not res['peer_group_target_links']):
                    res['peer_group_target_links'] = []
        return res
    
    @logged
    def validate_target(self, targetToSave, for_api = False):
        errors = []
        target = dict2row(Target, targetToSave, True)
        if (not target.name) or (len(target.name.strip()) <= 0):
            errors.append({'field': 'name', 'type': 'error','message': 'Name is not provided or is blank.'})
        if (not target.description) or (len(target.description.strip()) <= 0):
            errors.append({'field': 'description', 'type': 'error', 'message': 'Description is not provided or is blank.'})
        if (not target.ip_address) or (len(target.ip_address.strip()) <= 0):
            errors.append({'field': 'ip_address', 'type': 'error', 'message': 'IP-Address/Network is not provided or is blank.'})
        else:
            try:
                ip_address = ipaddress.ip_interface(target.ip_address)
            except:
                errors.append({'field': 'ip_address', 'type': 'error', 'message': 'IP-Address/Network is not valid.'})
        if (not target.peer_group_target_links) or (len(target.peer_group_target_links) <= 0):
            errors.append({'field': 'peer_groups', 'type': 'warning', 'message': 'No targets added.'})
        return errors

    @logged
    def saveTarget(self, targetToSave, for_api = False):
        with Session(self.engine) as session:
            target = dict2row(Target, targetToSave, True)
            target = session.merge(target)
            session.commit()
            res = row2dict(target) if for_api else target
            return res

    @logged
    def getServerConfigurations(self, for_api = False):
        with Session(self.engine) as session:
            stmt = select(ServerConfiguration)
            res = session.scalars(stmt).unique().all()
            res = [row2dict(x) for x in res] if for_api else res
            return res
    
    @logged
    def getServerConfiguration(self, id, for_api = False):
        with Session(self.engine) as session:
            stmt = select(ServerConfiguration).where(ServerConfiguration.id == id)
            res = list(session.scalars(stmt).unique().all())[0]
            res = row2dict(res) if for_api else res
            return res

    @logged
    def validate_server_configuration(self, serverConfigurationToSave, for_api = False):
        errors = []
        serverConfiguration = dict2row(ServerConfiguration, serverConfigurationToSave, True)

        if (not serverConfiguration.ip_address) or (len(serverConfiguration.ip_address.strip()) <= 0):
            errors.append({'field': 'ip_address', 'type': 'error', 'message': 'IP-Address/Network is not provided or is blank.'})
        else:
            try:
                ip_address = ipaddress.ip_interface(serverConfiguration.ip_address)
                if is_network_address(ip_address)[0]:
                    errors.append({'field': 'ip_address', 'type': 'error', 'message': f'IP-Address is a network address. "{serverConfiguration.ip_address}" is not a valid value.'})
            except:
                errors.append({'field': 'ip_address', 'type': 'error', 'message': 'IP-Address/Network is not valid.'})

        return errors

    @logged
    def saveServerConfiguration(self, serverConfigurationToSave, for_api = False):
        with Session(self.engine) as session:
            serverConfiguration = dict2row(ServerConfiguration, serverConfigurationToSave)
            serverConfiguration.ip_address = serverConfigurationToSave['ip_address']
            serverConfiguration = session.merge(serverConfiguration)
            session.commit()
            res = row2dict(serverConfiguration) if for_api else serverConfiguration
            return res
    
    @logged
    def getTargetsForIPTablesRules(self):
        with Session(self.engine) as session:
            opts_load_peers = joinedload(PeerGroup.peer_group_peer_links).options(joinedload(PeerGroupPeerLink.peer))
            opts_load_peergroups = joinedload(Target.peer_group_target_links).options(joinedload(PeerGroupTargetLink.peer_group).options(opts_load_peers))
            #opts2 = joinedload(Target.peer_group_target_links).options(joinedload(PeerGroupTargetLink.peer_group).options(joinedload(PeerGroup.peer_group_peer_links)))
            stmt = select(Target).options(opts_load_peergroups)
            targets = list(session.scalars(stmt).unique().all())
            return targets
