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
from wireguardhelper import WireGuardHelper

app = Flask(__name__, static_folder = FLASK_BASE_DIR,  )
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['DEBUG'] = True
app.config['TESTING'] = True
app.config['EXPLAIN_TEMPLATE_LOADING'] = False

   
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
    db = DbHelper()
    res = db.getPeers(for_api = True)
    return res

@app.route('/api/data/peer/<int:id>', methods = ['GET'])
@logged
def peer_get(id):
    db = DbHelper()
    res = db.getPeer(id, for_api = True)
    return res

@app.route('/api/data/peer', methods = ['POST'])
@logged
def peer_save():
    data = request.json
    db = DbHelper()
    errors = db.validate_peer(data, for_api = True)
    if [ x for x in errors if x['type'] == 'error']:
        return errors, 400
    res = db.savePeer(data, True)
    return res

@app.route('/api/data/peer-config-qr/<int:id>', methods = ['GET'])
@logged
def peer_get_config_qr(id):
    db = DbHelper()
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
    db = DbHelper()
    res = db.getPeerGroups(for_api = True)
    return res

@app.route('/api/data/peer_group/<int:id>', methods = ['GET'])
@logged
def peer_group_get(id):
    db = DbHelper()
    res = db.getPeerGroup(id, for_api = True)
    return res

@app.route('/api/data/peer_group', methods = ['POST'])
@logged
def peers_group_save():
    data = request.json
    db = DbHelper()
    errors = db.validate_peer_group(data, for_api = True)
    if [ x for x in errors if x['type'] == 'error']:
        return errors, 400
    res = db.savePeerGroup(data, for_api = True)
    return res

@app.route('/api/data/target', methods = ['GET'])
@logged
def targets():
    db = DbHelper()
    res = db.getTargets(for_api = True)
    return res

@app.route('/api/data/target/<int:id>', methods = ['GET'])
@logged
def target_get(id):
    db = DbHelper()
    res = db.getTarget(id, for_api = True)
    return res

@app.route('/api/data/target', methods = ['POST'])
@logged
def target_save():
    data = request.json
    db = DbHelper()
    errors = db.validate_target(data, for_api = True)
    if [ x for x in errors if x['type'] == 'error']:
        return errors, 400
    res = db.saveTarget(data, True)
    return res

@app.route('/api/data/server_configuration', methods = ['GET'])
@logged
def server_configurations():
    db = DbHelper()
    res = db.getServerConfigurations(for_api = True)
    return res

@app.route('/api/data/server_configuration/<int:id>', methods = ['GET'])
@logged
def server_configuration_get(id):
    db = DbHelper()
    res = db.getServerConfiguration(id, for_api = True)
    return res

@app.route('/api/data/server_configuration', methods = ['POST'])
@logged
def server_configuration_save():
    data = request.json
    db = DbHelper()
    errors = db.validate_server_configuration(data, for_api = True)
    if [ x for x in errors if x['type'] == 'error']:
        return errors, 400
    res = db.saveServerConfiguration(data, True)
    return res

@app.route('/api/data/wireguard_configuration', methods = ['GET'])
@logged
def wireguard_configuration_get():
    db = DbHelper()
    wg = WireGuardHelper(db)
    res = wg.getWireguardConfiguration()
    return res

@app.route('/api/control/generate_configuration_files', methods = ['GET'])
@logged
def generate_configuration_files():
    db = DbHelper()
    wg = WireGuardHelper(db)
    wg.generateConfigurationFiles()
    res = {'status': 'ok'}
    return res

@app.route('/api/control/wireguard_restart', methods = ['GET'])
@logged
def wireguard_restart():
    db = DbHelper()
    sc = db.getServerConfiguration(1)
    command = f'wg-quick down {sc.wireguard_config_path}; wg-quick up {sc.wireguard_config_path}; sudo conntrack -F; sudo conntrack -F; sudo conntrack -F;'
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
    return send_from_directory(FLASK_BASE_DIR, path)

@app.route('/')
@logged
def index():
    return app.send_static_file(FLASK_INDEX_RESOURCE)

@app.errorhandler(404)
def not_found_error(error):
    return app.send_static_file(FLASK_INDEX_RESOURCE)

if __name__ == "__main__":
    print(f'Flask base dir = {FLASK_BASE_DIR}')
    app.run(host = '0.0.0.0', port = 80)
