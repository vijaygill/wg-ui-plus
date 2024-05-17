#!/usr/bin/python
import os
import sys
import glob
import logging
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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def set_logging_verbose():
    logger.setLevel(logging.DEBUG)

SCRIPT_DIR = pathlib.Path().resolve() 

DB_FILE = '/data/wg-ui-plus.db'

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

DICT_DATA_TARGET_INTERNET = 'Internet'
DICT_DATA_TARGETS = [
        (DICT_DATA_TARGET_INTERNET, 'Internet', '0.0.0.0/0'),
        ]

SAMPLE_DATA_TARGETS = [
        ('Email Server', 'Email server', '192.168.0.33'),
        ('Database Server', 'Database server for developers', '192.168.0.34'),
        ('File Server', 'File server for common shared directories', '192.168.0.35'),
        ('Print Server', 'Print Server', '192.168.0.32'),
        ]

DICT_DATA_SERVER_CONFIGURATION = [
    (SERVER_HOST_NAME_DEFAULT, SERVER_HOST_IP_ADDRESS_DEFAULT, PORT_DEFAULT_INTERNAL, PORT_DEFAULT_EXTERNAL,
      '/config/wireguard/wg0.conf',
      '/config/wireguard/scripts/post-up.sh', 
      '/config/wireguard/scripts/post-down.sh'
      )
]

FLASK_BASE_DIR = '/clientapp'
FLASK_INDEX_RESOURCE = 'index.html'
