import os
import ipaddress
from functools import wraps
from dataclasses import dataclass
from flask import Flask, send_from_directory
from flask import request, jsonify
import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import Integer
from sqlalchemy import inspect
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

DB_FILE = './data/wg-ui-plus.db'

DICT_DATA_IPTABLES_CHAIN = [
        ('from-vip', 'All VIP Peers'),
        ('to-lan', 'LAN destinations'),
        ('to-internet', 'Internet destinations'),
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

def row2dict(row):
    #res = {c.name: getattr(row, c.name) for c in row.__table__.columns}
    res = { c.key: getattr(row, c.key) for c in inspect(row).mapper.column_attrs}
    return res

class Base(DeclarativeBase):
    pass

@dataclass
class PeerGroup(Base):
    __tablename__ = "wg_peer_groups"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))
    disabled: Mapped[Boolean] = mapped_column(Boolean)
    peers: Mapped[List["Peer"]] = relationship(back_populates = "peer_group", lazy = 'joined')

@dataclass
class Peer(Base):
    __tablename__ = "wg_peers"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    device_name:  Mapped[str] = mapped_column(String(255))
    ip_address_num: Mapped[int] = mapped_column(Integer)
    peer_group_id: Mapped[int] = mapped_column(ForeignKey("wg_peer_groups.id"))
    peer_group: Mapped["PeerGroup"] = relationship(back_populates = "peers", lazy = 'joined')

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
class IpTablesChain(Base):
    __tablename__ = "wg_iptables_chain"
    id: Mapped[int] = mapped_column(primary_key = True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))

    def __repr__(self) -> str:
        return f"IpTablesChain(id={self.id!r}, name={self.name!r})"

class DbRepo(object):
    def __init__(self):
        self.engine = create_engine(f'sqlite:///{DB_FILE}', echo = True)
        Base.metadata.create_all(self.engine)

        self.createDictionaryData()
        self.createSampleData()

    @logged
    def createDictionaryData(self):
        self.createDictionaryDataIpTablesChain()

    @logged
    def createDictionaryDataIpTablesChain(self):
        with Session(self.engine) as session:
            existing_rows = [ r.name for r in session.query( IpTablesChain ).all() ]
            rows_to_create = [ x for x in DICT_DATA_IPTABLES_CHAIN if x[0] not in existing_rows]

            for r in rows_to_create:
                name, description = r
                new_row = IpTablesChain( name = name, description = description )
                session.add(new_row)
                session.commit()

    @logged
    def createSampleData(self):
        peers = self.getPeers()
        if not peers:
            with Session(self.engine) as session:
                max_peer_groups = 3
                for i in range(0,max_peer_groups):
                    peer_group = PeerGroup(name = f'Peer Group - {i}' , description = f'Description - {i}', disabled = i == 3)
                    session.add(peer_group)
                    session.commit()
                peer_groups = [x for x in session.query( PeerGroup ).all()]
                for i in range(0, 10):
                    ip_address_num = 323223552 + 2 + i
                    peer = Peer(name = f'Peer - {i}', device_name = f'Device - {i}', ip_address = ip_address_num, peer_group = peer_groups[i % max_peer_groups] )
                    session.add(peer)
                    session.commit()

    @logged
    def getPeers(self):
        with Session(self.engine) as session:
            stmt = select(Peer)
            res = session.scalars(stmt).unique().all()
            return res
        
    @logged
    def getPeerGroups(self):
        with Session(self.engine) as session:
            stmt = select(PeerGroup)
            res = session.scalars(stmt).unique().all()
            return res
    @logged 
    def savePeerGroup(self, peerGroupToSave):
        with Session(self.engine) as session:
            if 'id' in peerGroupToSave.keys():
                peerGroup = PeerGroup(id = peerGroupToSave['id'], 
                                      name = peerGroupToSave['name'],
                                      description = peerGroupToSave['description'],
                                      disabled = peerGroupToSave['disabled'])
                peerGroup = session.merge(peerGroup)
            else:
                peerGroup = PeerGroup(name = peerGroupToSave['name'],
                                      description = peerGroupToSave['description'],
                                      disabled = peerGroupToSave['disabled'])
                peerGroup = session.add(peerGroup)
            session.commit()
            return peerGroup

    @logged
    def getIpTablesChains(self):
        with Session(self.engine) as session:
            res = session.query( IpTablesChain ).all()
            return res

row2dict = lambda r: {c.name: getattr(r, c.name) for c in r.__table__.columns}

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

@app.route('/api/data/iptablechains')
@logged
def iptablechain():
    db = DbRepo()
    res = db.getIpTablesChains()
    return res

@app.route('/api/data/peers')
@logged
def peers():
    db = DbRepo()
    res = [ {
        'id': x.id,
        'name': x.name,
        'device_name': x.device_name,
        'peer_group_id': x.peer_group_id,
        'peer_group': row2dict(x.peer_group),
        'ip_address_num': x.ip_address_num,
        'ip_address': x.ip_address,
        } for x in db.getPeers()]
    return res

@app.route('/api/data/peer_groups')
@logged
def peers_groups():
    db = DbRepo()
    pgs = [ (row2dict(x), [row2dict(p) for p in x.peers]) for x in db.getPeerGroups()]
    for pg, p in pgs:
        pg['peers'] = p
    res = [x[0] for x in pgs]
    return res

@app.route('/api/data/peer_group/save', methods = ['POST'])
@logged
def peers_group_save():
    data = request.json
    db = DbRepo()
    res = db.savePeerGroup(data)
    res = {'status': 'ok'}
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
