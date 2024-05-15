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

SCRIPT_DIR = pathlib.Path().resolve() 

DB_FILE = '/app/data/wg-ui-plus.db'

SAMPLE_MAX_PEER_GROUPS = 3
SAMPLE_MAX_PEERS = 5
IP_ADDRESS_BASE = 3232236033
PORT_DEFAULT_EXTERNAL = 1196
PORT_DEFAULT_INTERNAL = 51820
SERVER_HOST_NAME_DEFAULT = f'myvpn.duckdns.org'
SERVER_HOST_IP_ADDRESS_DEFAULT='192.168.2.1/24'

DICT_DATA_PEER_GROUP_EVERYONE = 'Everyone'

DICT_DATA_PEER_GROUPS = [
    (DICT_DATA_PEER_GROUP_EVERYONE, 'All Peers in the system', False, True)
]

SAMPLE_DATA_PEER_GROUPS = [
    ('Developers', 'All developers', True, True),
    ('Testers', 'All testers', True, True),
    ('Managers', 'All Managers', True, True),
]

IP_ADDRESS_INTERNET = '0.0.0.0/0'

DICT_DATA_TARGETS = [
        ('Internet', 'Internet', '0.0.0.0/0'),
        ]

SAMPLE_DATA_TARGETS = [
        ('Email Server', 'Email server', '192.168.0.33'),
        ('Database Server', 'Database server for developers', '192.168.0.34'),
        ('File Server', 'File server for common shared directories', '192.168.0.35'),
        ('Print Server', 'Print Server', '192.168.0.32'),
        ]

DICT_DATA_SERVER_CONFIGURATION = [
    (SERVER_HOST_NAME_DEFAULT, SERVER_HOST_IP_ADDRESS_DEFAULT, PORT_DEFAULT_INTERNAL, PORT_DEFAULT_EXTERNAL,
      '/app/wireguard/wg0.conf',
      '/app/wireguard/scripts/post-up.sh', 
      '/app/wireguard/scripts/post-down.sh'
      )
]

USE_SSR = False # Will get SSR working some other time

BASE_DIR_INFOS = [
        ('wg-ui-plus/dist/wg-ui-plus/browser', 'index.html'),
        ('wg-ui-plus/dist/wg-ui-plus/server', 'index.server.html'),
        ]

BASE_DIR_INFO = BASE_DIR_INFOS[1] if USE_SSR else BASE_DIR_INFOS[0]

BASE_DIR, INDEX_RESOURCE = BASE_DIR_INFO

app = Flask(__name__, static_folder = BASE_DIR,  )
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['DEBUG'] = True
app.config['TESTING'] = True
app.config['EXPLAIN_TEMPLATE_LOADING'] = False

def logged(func):
    @wraps(func)
    def logger_func(*args, **kwargs):
        func_name = func.__name__
        try:
            app.logger.info(f'***** {func_name}: start')
            res = func(*args, **kwargs)
            return res
        finally:
            app.logger.info(f'***** {func_name}: end')

    return logger_func

def row2dict(row, include_relations = True):
    cols = None
    self_insp = None
    try:
        self_insp = inspect(row)
        cols = self_insp.mapper.columns
    except NoInspectionAvailable:
        pass
    if not cols:
        return None
    res = {}
    for col in cols:
        value = getattr(row, col.key)
        if isinstance(value, (list, tuple)):
            res[col.key] = [row2dict(item) for item in value]
        else:
            res[col.key] = value
    relationships = inspect(row).mapper.relationships.items()
    for k,col in relationships:
        if not include_relations:
            continue
        if (self_insp.unloaded) and (col.key in self_insp.unloaded):
            continue
        value = getattr(row, col.key)
        if isinstance(value, (list, tuple)):
            if value:
                res[col.key] = [row2dict(item) for item in value]
            else:
                res[col.key] = []
        else:
            try:
                res[col.key] = row2dict(value, include_relations = False)
            except NoInspectionAvailable:
                pass
            pass
    hybrids = [ (k, v) for k, v in inspect(row).mapper.all_orm_descriptors.items() if v.extension_type == sqlalchemy.ext.hybrid.HybridExtensionType.HYBRID_PROPERTY]
    for k, col in hybrids:
        value = getattr(row, k)
        res[k] = value
    return res

def dict2row(classType, dictToSave, include_relations = False):
    insp = inspect(classType)
    res = classType()
    cols = [ col for col in insp.mapper.column_attrs if col.key in dictToSave.keys()]
    for col in cols:
        value = dictToSave[col.key]
        # if value is a list/tuple, then get dict2row for each item in it
        # else just set it as simple value
        if isinstance(value, (list, tuple, dict)):
            setattr(res, col.key, [dict2row(col.type, item) for item in value])
        else:
            setattr(res, col.key, value)

    relationships = insp.mapper.relationships.items()
    for key, col in relationships:
        if not include_relations:
            continue
        value = dictToSave[key] if key in dictToSave.keys() else None
        if col.direction == sqlalchemy.orm.interfaces.ONETOMANY:
            if value:
                items = [ dict2row(col.entity.entity,x) for x in value]
                setattr(res, col.key, items)

    return res

def is_network_address(addr):
    addr = ipaddress.ip_interface(addr)
    res = int(addr.ip) == int(addr.network.network_address) and addr.network.prefixlen < 32
    return (res, addr.ip, addr.network)

@logged
def ensure_folder_exists_for_file(filepath):
    dir = os.path.dirname(filepath)
    if not os.path.exists(dir):
        os.makedirs(dir)
        app.logger.warning(f'Directory was missing. Created: {dir}')

def generate_keys():
    # generate private key
    private_key = X25519PrivateKey.generate()
    private_bytes = private_key.private_bytes( encoding = serialization.Encoding.Raw, format = serialization.PrivateFormat.Raw, encryption_algorithm = serialization.NoEncryption())
    key_private = codecs.encode(private_bytes, 'base64').decode('utf8').strip()

    # derive public key
    public_bytes = private_key.public_key().public_bytes(encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw)
    key_public = codecs.encode(public_bytes, 'base64').decode('utf8').strip()
    return (key_public, key_private)

class Base(DeclarativeBase):
    pass

@dataclass
class PeerGroup(Base):
    __tablename__ = "wg_peer_group"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))
    disabled: Mapped[Boolean] = mapped_column(Boolean, nullable = True)
    allow_modify_self : Mapped[Boolean] = mapped_column(Boolean, nullable = True)
    allow_modify_peers: Mapped[Boolean] = mapped_column(Boolean, nullable = True)
    allow_modify_targets: Mapped[Boolean] = mapped_column(Boolean, nullable = True)
    peer_group_peer_links: Mapped[List["PeerGroupPeerLink"]] = relationship(back_populates="peer_group", cascade="all, delete-orphan")
    peer_group_target_links: Mapped[List["PeerGroupTargetLink"]] = relationship(back_populates="peer_group", cascade="all, delete-orphan")

@dataclass
class Peer(Base):
    __tablename__ = "wg_peer"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    ip_address: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer)
    disabled: Mapped[Boolean] = mapped_column(Boolean, nullable = True)
    public_key: Mapped[str] = mapped_column(String(255), nullable = True)
    private_key: Mapped[str] = mapped_column(String(255), nullable = True)
    peer_group_peer_links: Mapped[List["PeerGroupPeerLink"]] = relationship(back_populates="peer", cascade="all, delete-orphan")

@dataclass
class PeerGroupPeerLink(Base):
    __tablename__ = "wg_peer_group_peer_link"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    peer_group_id: Mapped[int] = mapped_column(ForeignKey("wg_peer_group.id"))
    peer_group: Mapped["PeerGroup"] = relationship()
    peer_id: Mapped[int] = mapped_column(ForeignKey("wg_peer.id"))
    peer: Mapped["Peer"] = relationship()

@dataclass
class Target(Base):
    __tablename__ = "wg_target"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))
    ip_address: Mapped[str] = mapped_column(String(255))
    disabled: Mapped[Boolean] = mapped_column(Boolean, nullable = True)
    allow_modify_self: Mapped[Boolean] = mapped_column(Boolean, nullable = True)
    allow_modify_peer_groups: Mapped[Boolean] = mapped_column(Boolean, nullable = True)
    peer_group_target_links: Mapped[List["PeerGroupTargetLink"]] = relationship(back_populates="target", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"Target(id={self.id!r}, name={self.name!r}, address={self.ip_address!r})"

@dataclass
class PeerGroupTargetLink(Base):
    __tablename__ = "wg_peer_group_target_link"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    peer_group_id: Mapped[int] = mapped_column(ForeignKey("wg_peer_group.id"))
    peer_group: Mapped["PeerGroup"] = relationship()
    target_id: Mapped[int] = mapped_column(ForeignKey("wg_target.id"))
    target: Mapped["Target"] = relationship()

@dataclass
class ServerConfiguration(Base):
    __tablename__ = "wg_server_configuration"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    ip_address: Mapped[str] = mapped_column(String(255))
    host_name_external: Mapped[str] = mapped_column(String(255))
    port_external: Mapped[int] = mapped_column(Integer)
    port_internal: Mapped[int] = mapped_column(Integer)
    wireguard_config_path: Mapped[str] = mapped_column(String(255))
    script_path_post_down: Mapped[str] = mapped_column(String(255))
    script_path_post_up: Mapped[str] = mapped_column(String(255))
    public_key: Mapped[str] = mapped_column(String(255), nullable = True)
    private_key: Mapped[str] = mapped_column(String(255), nullable = True)
    peer_default_port : Mapped[int] = mapped_column(Integer)

    def __repr__(self) -> str:
        return f"ServerConfiguration(id={self.id!r}, ip_address={self.ip_address!r}, port={self.port!r})"

class DbRepo(object):
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
        self.createDictionaryDataPeerGroups()
        self.createDictionaryDataTargets()
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
                # add client side config also.
                sc = self.getServerConfiguration(1)
                wg = WireGuardHelper(self)
                s, c = wg.getWireguardConfigurationsForPeer(sc, peer)
                res['peer_configuration'] = c
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

@app.route('/test')
@logged
def test():
    return 'Hello, World!'

@app.route('/test-qr')
@logged
def testqr():
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=5)
    qr.add_data('Hello, World!')
    qr.make(fit = True)
    img = qr.make_image(fill_color="black", back_color="white")
    byteIO = BytesIO()
    img.save(byteIO, 'PNG')
    byteIO.seek(0)
    return send_file(byteIO, mimetype='image/png')

@app.route('/api/docker/container/list')
@logged
def docker_container_list():
    client = docker.DockerClient(base_url = 'unix://var/run/docker.sock')
    res = [ {
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "short_id": c.short_id,
        } for c in client.containers.list( all = True, ignore_removed = True) ]
    res.sort(key = lambda x : x['name'] )
    return res

@app.route('/api/docker/container/start')
@logged
def docker_container_start(name = None):
    name = request.args.get('name')
    client = docker.DockerClient(base_url = 'unix://var/run/docker.sock')
    container = client.containers.get(name)
    container.start()
    return { 'status': 'ok' } #docker_container_list()

@app.route('/api/docker/container/stop')
@logged
def docker_container_stop(name = None):
    name = request.args.get('name')
    client = docker.DockerClient(base_url = 'unix://var/run/docker.sock')
    container = client.containers.get(name)
    container.stop()
    return { 'status': 'ok' } #docker_container_list()

@app.route('/api/data/peer', methods = ['GET'])
@logged
def peers():
    db = DbRepo()
    res = db.getPeers(for_api = True)
    return res

@app.route('/api/data/peer/<int:id>', methods = ['GET'])
@logged
def peer_get(id):
    db = DbRepo()
    res = db.getPeer(id, for_api = True)
    return res

@app.route('/api/data/peer', methods = ['POST'])
@logged
def peer_save():
    data = request.json
    db = DbRepo()
    errors = db.validate_peer(data, for_api = True)
    if [ x for x in errors if x['type'] == 'error']:
        return errors, 400
    res = db.savePeer(data, True)
    return res

@app.route('/api/data/peer-config-qr/<int:id>', methods = ['GET'])
@logged
def peer_get_config_qr(id):
    db = DbRepo()
    wg = WireGuardHelper(db)
    serverConfiguration = db.getServerConfiguration(1)
    peer = db.getPeer(id)
    s,c = wg.getWireguardConfigurationsForPeer(serverConfiguration, peer)
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=5)
    qr.add_data(c)
    qr.make(fit = True)
    img = qr.make_image(fill_color="black", back_color="white")
    byteIO = BytesIO()
    img.save(byteIO, 'PNG')
    byteIO.seek(0)
    return send_file(byteIO, mimetype='image/png')


@app.route('/api/data/peer_group')
@logged
def peers_groups():
    db = DbRepo()
    res = db.getPeerGroups(for_api = True)
    return res

@app.route('/api/data/peer_group/<int:id>', methods = ['GET'])
@logged
def peer_group_get(id):
    db = DbRepo()
    res = db.getPeerGroup(id, for_api = True)
    return res

@app.route('/api/data/peer_group', methods = ['POST'])
@logged
def peers_group_save():
    data = request.json
    db = DbRepo()
    errors = db.validate_peer_group(data, for_api = True)
    if [ x for x in errors if x['type'] == 'error']:
        return errors, 400
    res = db.savePeerGroup(data, for_api = True)
    return res

@app.route('/api/data/target', methods = ['GET'])
@logged
def targets():
    db = DbRepo()
    res = db.getTargets(for_api = True)
    return res

@app.route('/api/data/target/<int:id>', methods = ['GET'])
@logged
def target_get(id):
    db = DbRepo()
    res = db.getTarget(id, for_api = True)
    return res

@app.route('/api/data/target', methods = ['POST'])
@logged
def target_save():
    data = request.json
    db = DbRepo()
    errors = db.validate_target(data, for_api = True)
    if [ x for x in errors if x['type'] == 'error']:
        return errors, 400
    res = db.saveTarget(data, True)
    return res

@app.route('/api/data/server_configuration', methods = ['GET'])
@logged
def server_configurations():
    db = DbRepo()
    res = db.getServerConfigurations(for_api = True)
    return res

@app.route('/api/data/server_configuration/<int:id>', methods = ['GET'])
@logged
def server_configuration_get(id):
    db = DbRepo()
    res = db.getServerConfiguration(id, for_api = True)
    return res

@app.route('/api/data/server_configuration', methods = ['POST'])
@logged
def server_configuration_save():
    data = request.json
    db = DbRepo()
    res = db.saveServerConfiguration(data, True)
    return res

@app.route('/api/data/wireguard_configuration', methods = ['GET'])
@logged
def wireguard_configuration_get():
    db = DbRepo()
    wg = WireGuardHelper(db)
    res = wg.getWireguardConfiguration()
    return res

@app.route('/api/control/generate_configuration_files', methods = ['GET'])
@logged
def generate_configuration_files():
    db = DbRepo()
    wg = WireGuardHelper(db)
    wg.generateConfigurationFiles()
    res = {'status': 'ok'}
    return res

@app.route('/api/control/wireguard_restart', methods = ['GET'])
@logged
def wireguard_restart():
    command = 'wg-quick down /app/wireguard/wg0.conf; wg-quick up /app/wireguard/wg0.conf; sudo conntrack -F; sudo conntrack -F; sudo conntrack -F;'
    output = ''
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    try:
        outs, errs = proc.communicate(timeout = 60)
        output = outs.decode('utf-8') + errs.decode('utf-8')
    except subprocess.TimeoutExpired:
        proc.kill()
    app.logger.warn(f'output: {output}')
    res = {'status': 'ok', 'output': output }
    res = jsonify(res)
    return res

@app.route('/<path:path>', methods=['GET'])
@logged
def serve_static_files(path):
    app.logger.info(f'serve_static_files: {path}')
    return send_from_directory(BASE_DIR, path)

@app.route('/')
@logged
def index():
    return app.send_static_file(INDEX_RESOURCE)

@app.errorhandler(404)
def not_found_error(error):
    return app.send_static_file(INDEX_RESOURCE)

if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 80)
