import os
from functools import wraps
from dataclasses import dataclass
from flask import Flask, send_from_directory
from flask import request
import sqlalchemy
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy import select

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

class Base(DeclarativeBase):
    pass

@dataclass
class Peer(Base):
    __tablename__ = "wg_peers"
    id: Mapped[int] = mapped_column(primary_key = True)
    name: Mapped[str] = mapped_column(String(255))
    device_name:  Mapped[str] = mapped_column(String(255))
    is_vip:  Mapped[bool] = mapped_column(Boolean, nullable = True)

    def __repr__(self) -> str:
        return f"Peer(id={self.id!r}, name={self.name!r}, fullname={self.device_name!r})"

@dataclass
class IpTablesChain(Base):
    __tablename__ = "wg_iptables_chain"
    id: Mapped[int] = mapped_column(primary_key = True)
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
                for i in range(0,10):
                    peer = Peer(name = f'Peer - {i}', device_name = f'Device - {i}')
                    if i % 4 == 0:
                        peer = Peer(name = f'Peer - {i}', device_name = f'Device - {i}', is_vip = True)
                    session.add(peer)
                    session.commit()

    @logged
    def getPeers(self):
        with Session(self.engine) as session:
            res = session.query( Peer ).all()
            return res

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
    return res

@app.route('/api/docker/container/start')
@logged
def docker_container_start(name = None):
    #client = docker.DockerClient(base_url = 'unix://var/run/docker.sock')
    #res = [ c.name for c in client.containers.list() ]
    name = request.args.get('name')
    res = { 'x': name }
    return res

@app.route('/api/docker/container/stop')
@logged
def docker_container_stop(name = None):
    #client = docker.DockerClient(base_url = 'unix://var/run/docker.sock')
    #res = [ c.name for c in client.containers.list() ]
    res = { 'x': name }
    return res

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
    res = db.getPeers()
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
