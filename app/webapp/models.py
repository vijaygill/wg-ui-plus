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
