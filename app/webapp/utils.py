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

def logged(func):
    @wraps(func)
    def logger_func(*args, **kwargs):
        func_name = func.__name__
        try:
            logger.info(f'***** {func_name}: start')
            res = func(*args, **kwargs)
            return res
        finally:
            logger.info(f'***** {func_name}: end')

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

