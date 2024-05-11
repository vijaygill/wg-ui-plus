#!/usr/bin/python
import os
import ipaddress
from functools import wraps
from dataclasses import dataclass
import random
from flask import Flask, send_from_directory
from flask import request, jsonify
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
from sqlalchemy.ext.hybrid import hybrid_method
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from typing import List
import docker
import pathlib
import codecs
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives import serialization

SCRIPT_DIR = pathlib.Path().resolve() 

DB_FILE = os.path.join(SCRIPT_DIR, 'data/wg-ui-plus.db')

SAMPLE_MAX_PEER_GROUPS = 3
SAMPLE_MAX_PEERS = 5
IP_ADDRESS_BASE = 3232236033
PORT_DEFAULT_PEER = 1195
PORT_DEFAULT_SERVER = 51820


DICT_DATA_PEER_GROUPS = [
    ('All', 'All')
]
DICT_DATA_TARGET_GROUPS = [
        ('to-lan', 'LAN destinations'),
        ('to-internet', 'Internet destinations'),
        ]

DICT_DATA_TARGETS = [
        ('All Targets', 'All targets', '0.0.0.0/0')
        ]

DICT_DATA_SERVER_CONFIGURATION = [
    ('192.168.2.1', PORT_DEFAULT_SERVER,
      os.path.join(SCRIPT_DIR, '/wireguard/scripts/post-up.sh'), 
      os.path.join(SCRIPT_DIR, '/wireguard/scripts/post-down.sh')
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
        d = inspect(row).dict
    except:
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
        value = getattr(row, col.key)
        if isinstance(value, (list, tuple)):
            res[col.key] = [row2dict(item) for item in value]
        else:
            try:
                insp = inspect(value)
                res[col.key] = row2dict(value, include_relations = False)
            except:
                pass
            pass
    hybrids = [ (k, v) for k, v in inspect(row).mapper.all_orm_descriptors.items() if v.extension_type == sqlalchemy.ext.hybrid.HybridExtensionType.HYBRID_PROPERTY]
    for k, col in hybrids:
        value = getattr(row, k)
        res[k] = value
    return res

def dict2row(classType, dictToSave):
    res = classType()
    cols = [ col for col in inspect(classType).mapper.column_attrs if col.key in dictToSave.keys()]
    for col in cols:
        value = dictToSave[col.key]
        # if value is a list/tuple, then get dict2row for each item in it
        # else just set it as simple value
        if isinstance(value, (list, tuple)):
            setattr(res, col.key, [dict2row(col.type, item) for item in value])
        else:
            setattr(res, col.key, value)
    return res

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
class PeerGroupPeerLink(Base):
    __tablename__ = "wg_peer_group_peer_link"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    peer_group_id: Mapped[int] = mapped_column(ForeignKey("wg_peer_group.id"))
    peer_group: Mapped["PeerGroup"] = relationship(lazy = 'joined')
    peer_id: Mapped[int] = mapped_column(ForeignKey("wg_peer.id"))
    peer: Mapped["Peer"] = relationship(lazy = 'joined')

@dataclass
class PeerGroup(Base):
    __tablename__ = "wg_peer_group"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))
    disabled: Mapped[Boolean] = mapped_column(Boolean, nullable = True)
    peer_group_peer_links: Mapped[List["PeerGroupPeerLink"]] = relationship(back_populates="peer_group")
    is_inbuilt: Mapped[Boolean] = mapped_column(Boolean, nullable = True)

@dataclass
class Peer(Base):
    __tablename__ = "wg_peer"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    device_name:  Mapped[str] = mapped_column(String(255))
    ip_address_num: Mapped[int] = mapped_column(Integer)
    port: Mapped[int] = mapped_column(Integer)
    disabled: Mapped[Boolean] = mapped_column(Boolean, nullable = True)
    public_key: Mapped[str] = mapped_column(String(255), nullable = True)
    private_key: Mapped[str] = mapped_column(String(255), nullable = True)
    peer_group_peer_links: Mapped[List["PeerGroupPeerLink"]] = relationship(back_populates="peer")

    @hybrid_property
    def ip_address(self):
        # TODO: I don't like this. Review later
        try:
            return str(ipaddress.ip_address(self.ip_address_num))
        except:
            pass

        return None

    @ip_address.setter
    def ip_address(self, value):
        self.ip_address_num = int(ipaddress.ip_address(value))

    def __repr__(self) -> str:
        return f"Peer(id={self.id!r}, name={self.name!r}, fullname={self.device_name!r})"
    
@dataclass
class TargetGroupTargetLink(Base):
    __tablename__ = "wg_target_group_target_link"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    target_group_id: Mapped[int] = mapped_column(ForeignKey("wg_target_group.id"))
    target_group: Mapped["TargetGroup"] = relationship(lazy = 'joined')
    target_id: Mapped[int] = mapped_column(ForeignKey("wg_target.id"))
    target: Mapped["Target"] = relationship(lazy = 'joined')

@dataclass
class TargetGroup(Base):
    __tablename__ = "wg_target_group"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))
    disabled: Mapped[Boolean] = mapped_column(Boolean, nullable = True)
    target_group_target_links: Mapped[List["TargetGroupTargetLink"]] = relationship(back_populates="target_group")
    is_inbuilt: Mapped[Boolean] = mapped_column(Boolean, nullable = True)

@dataclass
class Target(Base):
    __tablename__ = "wg_target"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))
    ip_network: Mapped[str] = mapped_column(String(255))
    disabled: Mapped[Boolean] = mapped_column(Boolean, nullable = True)
    target_group_target_links: Mapped[List["TargetGroupTargetLink"]] = relationship(back_populates="target")
    is_inbuilt: Mapped[Boolean] = mapped_column(Boolean, nullable = True)

    def __repr__(self) -> str:
        return f"Target(id={self.id!r}, name={self.name!r}, fullname={self.ip_network!r})"

@dataclass
class ServerConfiguration(Base):
    __tablename__ = "wg_server_configuration"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    ip_address_num: Mapped[int] = mapped_column(Integer)
    port: Mapped[int] = mapped_column(Integer)
    script_path_post_down: Mapped[str] = mapped_column(String(255))
    script_path_post_up: Mapped[str] = mapped_column(String(255))
    public_key: Mapped[str] = mapped_column(String(255), nullable = True)
    private_key: Mapped[str] = mapped_column(String(255), nullable = True)
    peer_default_port : Mapped[int] = mapped_column(Integer)

    @hybrid_property
    def ip_address(self):
        # TODO: I don't like this. Review later
        try:
            return str(ipaddress.ip_address(self.ip_address_num))
        except:
            pass

        return None

    @ip_address.setter
    def ip_address(self, value):
        self.ip_address_num = int(ipaddress.ip_address(value))


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
        db_dir = os.path.dirname(self.db_file)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
            app.logger.warning(f'DB directory was missing. Created: {db_dir}')
        self.engine = create_engine(f'sqlite:///{DB_FILE}', echo = True)
        Base.metadata.create_all(self.engine)

    @logged
    def createDictionaryData(self):
        self.createDictionaryDataPeerGroups()
        self.createDictionaryDataTargetGroups()
        self.createDictionaryDataTargets()
        self.createDictionaryDataServerConfiguration()

    @logged
    def createDictionaryDataServerConfiguration(self):
        with Session(self.engine) as session:
            existing_rows = [ r.name for r in session.query( ServerConfiguration ).all() ]
            rows_to_create = [ x for x in DICT_DATA_SERVER_CONFIGURATION if x[0] not in existing_rows]
            for r in rows_to_create:
                ip_address, port, script_path_post_up, script_path_post_down = r
                public_key, private_key = generate_keys()
                new_row = ServerConfiguration( ip_address = ip_address, port = port, script_path_post_up = script_path_post_up, 
                                              script_path_post_down = script_path_post_down, 
                                              public_key = public_key, private_key = private_key,
                                              peer_default_port = PORT_DEFAULT_PEER )
                session.add(new_row)
                session.commit()
        pass

    @logged
    def createDictionaryDataPeerGroups(self):
        with Session(self.engine) as session:
            existing_rows = [ r.name for r in session.query( PeerGroup ).all() ]
            rows_to_create = [ x for x in DICT_DATA_PEER_GROUPS if x[0] not in existing_rows]

            for r in rows_to_create:
                name, description = r
                new_row = PeerGroup( name = name, description = description, is_inbuilt = True )
                session.add(new_row)
                session.commit()

    @logged
    def createDictionaryDataTargetGroups(self):
        with Session(self.engine) as session:
            existing_rows = [ r.name for r in session.query( TargetGroup ).all() ]
            rows_to_create = [ x for x in DICT_DATA_TARGET_GROUPS if x[0] not in existing_rows]

            for r in rows_to_create:
                name, description = r
                new_row = TargetGroup( name = name, description = description, is_inbuilt = True )
                session.add(new_row)
                session.commit()

    @logged
    def createDictionaryDataTargets(self):
        with Session(self.engine) as session:
            existing_rows = [ r.name for r in session.query( Target ).all() ]
            rows_to_create = [ x for x in DICT_DATA_TARGETS if x[0] not in existing_rows]

            for r in rows_to_create:
                name, description, ip_network = r
                new_row = Target( name = name, description = description, ip_network = ip_network, is_inbuilt = True )
                session.add(new_row)
                session.commit()
				
    @logged
    def createSampleData(self):
        peers = self.getPeers()
        if not peers:
            with Session(self.engine) as session:
                SAMPLE_MAX_PEER_GROUPS = 3
                SAMPLE_MAX_PEERS = 5
                max_peer_groups = SAMPLE_MAX_PEER_GROUPS
                for i in range(0,max_peer_groups):
                    peer_groups = [(f'Peer - {x}', f'Description {x}') for x in range(0,max_peer_groups)]
                    peer_group = PeerGroup(name = f'Peer Group - {i}' , description = f'Description - {i}', disabled = i == 3)
                    session.add(peer_group)
                    session.commit()
                
                serverConfiguration = self.getServerConfiguration(1)
                for i in range(0, SAMPLE_MAX_PEERS):
                    ip_address_num = IP_ADDRESS_BASE + 2 + i
                    public_key, private_key = generate_keys()
                    peer = Peer(name = f'Peer - {i}', device_name = f'Device - {i}', 
                                ip_address = ip_address_num, port = serverConfiguration.peer_default_port,
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
    def getPeer(self, id):
        with Session(self.engine) as session:
            stmt = select(Peer).where(Peer.id == id)
            res = list(session.scalars(stmt).unique().all())[0]
            res = row2dict(res)
            #res['lookup_peer_group'] = [ row2dict(x) for x in self.getPeerGroups() ]
            return res

    @logged
    def savePeer(self, peerToSave):
        with Session(self.engine) as session:
            stmt = sqlalchemy.select(func.max(Peer.ip_address_num))
            ip_address_num_max = session.scalars(stmt).unique().all()
            ip_address_num_max = ip_address_num_max[0] if ip_address_num_max else IP_ADDRESS_BASE
            peer = dict2row(Peer, peerToSave)
            if peer.ip_address_num is None:
                ip_address_num = ip_address_num_max + 1
                peer.ip_address = ip_address_num
            peer = session.merge(peer)
            session.commit()
            return peer

    @logged
    def getPeerGroups(self, for_api = False):
        with Session(self.engine) as session:
            stmt = select(PeerGroup)
            res = session.scalars(stmt).unique().all()
            if(for_api):
                res = [row2dict(x) for x in res]
            return res

    @logged
    def getPeerGroup(self, id):
        with Session(self.engine) as session:
            stmt = select(PeerGroup).where(PeerGroup.id == id)
            res = list(session.scalars(stmt).unique().all())[0]
            res = row2dict(res)
            return res

    @logged 
    def savePeerGroup(self, dictToSave):
        with Session(self.engine) as session:
            item = dict2row(PeerGroup, dictToSave)
            item = session.merge(item)
            session.commit()
            return item

    @logged
    def getTargetGroups(self, for_api = False):
        with Session(self.engine) as session:
            stmt = select(TargetGroup)
            res = session.scalars(stmt).unique().all()
            res = [row2dict(x) for x in res] if for_api else res
            return res
    
    @logged
    def getTargetGroup(self, id):
        with Session(self.engine) as session:
            stmt = select(TargetGroup).where(TargetGroup.id == id)
            res = list(session.scalars(stmt).unique().all())[0]
            res = row2dict(res)
            res['lookup_target_group'] = [ row2dict(x) for x in self.getTargetGroups() ]
            return res

    @logged
    def saveTargetGroup(self, target_groupToSave):
        with Session(self.engine) as session:
            target_group = dict2row(TargetGroup, target_groupToSave)
            target_group = session.merge(target_group)
            session.commit()
            return target_group

    @logged
    def getTargets(self, for_api = False):
        with Session(self.engine) as session:
            stmt = select(Target)
            res = session.scalars(stmt).unique().all()
            res = [row2dict(x) for x in res] if for_api else res
            return res
    
    @logged
    def getTarget(self, id):
        with Session(self.engine) as session:
            stmt = select(Target).where(Target.id == id)
            res = list(session.scalars(stmt).unique().all())[0]
            res = row2dict(res)
            return res

    @logged
    def saveTarget(self, targetToSave):
        with Session(self.engine) as session:
            target = dict2row(Target, targetToSave)
            target = session.merge(target)
            session.commit()
            return target

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
    def saveServerConfiguration(self, serverConfigurationToSave):
        with Session(self.engine) as session:
            serverConfiguration = dict2row(ServerConfiguration, serverConfigurationToSave)
            serverConfiguration.ip_address = serverConfigurationToSave['ip_address']
            serverConfiguration = session.merge(serverConfiguration)
            session.commit()
            return serverConfiguration
    
    @logged
    def getWireguardConfigurationForServer(self, serverConfiguration):
        server_config = [
            f'# Generated for test purposes only.',
            f'# Will be removed once file can be consumed by WG.',
            f'[Interface]',
            f'Address = {serverConfiguration.ip_address}',
            f'ListenPort = {serverConfiguration.port}',
            f'PrivateKey = {serverConfiguration.public_key}',
            f'',
            f'PostUp = {serverConfiguration.script_path_post_up}',
            f'PostDown = {serverConfiguration.script_path_post_down}',
            f'',
        ]
        res = '\n'.join(server_config)
        return res

    @logged
    def getWireguardConfigurationsForPeer(self, serverConfiguration, peer):
        # returns tuple of server-side and client-side configurations
        peer_config_server_side = [
            f'# {peer.name}: disabled',
            f'',
            ] if peer.disabled else [
            f'[Peer]',
            f'# {peer.name} - the other side of the pipe',
            f'PublicKey = {peer.public_key}',
            #f'#PresharedKey = <this is optional>',
            f'AllowedIPs = {peer.ip_address}/32',
            f'PersistentKeepalive = 25',
            f'',
            f'',
        ]
        peer_config_server_side = '\n'.join(peer_config_server_side)

        peer_config_client_side = [
            f'# Generated for test purposes only.',
            f'# Will be removed once file can be consumed by WG.',
            f'[Interface]',
            f'Address = {peer.ip_address}',
            f'ListenPort = {peer.port}',
            f'PrivateKey = {peer.public_key}',
            f'',
            f'',
            f'[Peer]',
            f'# the other side of the pipe',
            f'PublicKey = {serverConfiguration.public_key}',
            f'Endpoint = {serverConfiguration.ip_address}/32',
            f'AllowedIPs = 0.0.0.0/0',
        ]
        peer_config_client_side = '\n'.join(peer_config_client_side)
        res = (peer_config_server_side, peer_config_client_side)
        return res

    @logged
    def getWireguardConfiguration(self):
        
        serverConfiguration = self.getServerConfiguration(1)
        server_config = self.getWireguardConfigurationForServer(serverConfiguration)

        # now generate configs for peers
        # both for the server side and client side
        peer_configs = []
        peers = self.getPeers()
        for peer in peers:
            peer_config_server_side, peer_config_client_side = self.getWireguardConfigurationsForPeer(serverConfiguration, peer)
            server_config += peer_config_server_side
            peer_configs += [peer_config_client_side]

        res = {}
        res['serverConfiguration'] = server_config
        res['peerConfigurations'] = peer_configs
        return res


@app.route('/test')
@logged
def test():
    return 'Hello, World!'

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
    res = db.getPeer(id)
    return res

@app.route('/api/data/peer', methods = ['POST'])
@logged
def peer_save():
    data = request.json
    db = DbRepo()
    res = db.savePeer(data)
    res = {'status': 'ok'}
    return res

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
    res = db.getPeerGroup(id)
    return res

@app.route('/api/data/peer_group', methods = ['POST'])
@logged
def peers_group_save():
    data = request.json
    db = DbRepo()
    res = db.savePeerGroup(data)
    res = {'status': 'ok'}
    return res

@app.route('/api/data/target_group', methods = ['GET'])
@logged
def target_groups():
    db = DbRepo()
    res = db.getTargetGroups(for_api = True)
    return res

@app.route('/api/data/target_group/<int:id>', methods = ['GET'])
@logged
def target_group_get(id):
    db = DbRepo()
    res = db.getTargetGroup(id)
    return res

@app.route('/api/data/target_group', methods = ['POST'])
@logged
def target_group_save():
    data = request.json
    db = DbRepo()
    res = db.saveTargetGroup(data)
    res = {'status': 'ok'}
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
    res = db.getTarget(id)
    return res

@app.route('/api/data/target', methods = ['POST'])
@logged
def target_save():
    data = request.json
    db = DbRepo()
    res = db.saveTarget(data)
    res = {'status': 'ok'}
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
    res = db.saveServerConfiguration(data)
    res = {'status': 'ok'}
    return res

@app.route('/api/data/wireguard_configuration', methods = ['GET'])
@logged
def wireguard_configuration_get():
    db = DbRepo()
    res = db.getWireguardConfiguration()
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
