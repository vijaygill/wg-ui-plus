import ipaddress

from django.core.exceptions import ValidationError
from django.db import models

from .util import (get_target_ip_address_parts,
                   is_network_address, is_single_address)
from .wireguardhelper import generate_keys


def validator_is_network_address(value, throw_exception=True):
    ip = None
    res = False
    try:
        ip = ipaddress.ip_interface(str(value))
        if isinstance(value, (ipaddress.IPv4Interface)):
            ip = value
        res = (
            int(ip.ip) == int(ip.network.network_address) and ip.network.prefixlen < 32
        )
    except:
        res = False
    if (not res) and throw_exception:
        raise ValidationError(
            f"{value} is not a valid network address. Example 192.168.2.0/24.",
            params={"value": value},
        )
    return res


def validator_are_network_addresses(value, throw_exception=True):
    res = False
    if value:
        parts = [x for x in value.split(",") if x]
        parts_result = [
            (x, validator_is_network_address(x, throw_exception=False)) for x in parts
        ]
        bad_values = [x[0] for x in parts_result if not x[1]]
        error_message = "Invalid value: " + ", ".join(bad_values)
        res = not bad_values
        if (not res) and throw_exception:
            raise ValidationError(
                f"{error_message}",
                params={"value": bad_values},
            )
    return res


def validator_is_single_address(value, throw_exception=True):
    res = is_single_address(value)
    if (not res) and throw_exception:
        raise ValidationError(
            f"{value} is not a valid IP address. Example 192.168.0.10.",
            params={"value": value},
        )
    return res


def validator_is_network_or_single_address(value):
    res = validator_is_network_address(value, False) or validator_is_single_address(value, False)
    if not res:
        raise ValidationError(
            f"{value} is not a valid IP address or network address. Example 192.168.0.10 Or 192.168.0.0/24.",
            params={"value": value},
        )


def validator_is_valid_target_ip_address(value):
    parts = get_target_ip_address_parts(value=value)
    res = parts[0]
    error = parts[-1]
    if (not res):
        raise ValidationError(
            f"{value} is not a valid IP address. Error: {error}",
            params={"value": value},
        )
    return res


# Create your models here.
class PeerGroup(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True)
    disabled = models.BooleanField(null=True, default=False)
    allow_modify_self = models.BooleanField(null=True, default=True)
    allow_modify_peers = models.BooleanField(null=True, default=True)
    allow_modify_targets = models.BooleanField(null=True, default=True)
    last_changed_datetime = models.DateTimeField(
        auto_now=True,
    )
    peers = models.ManyToManyField("Peer", blank=True)
    targets = models.ManyToManyField("Target", blank=True)

    def __str__(self):
        return f"{self.name} - {self.description}"


class Peer(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True)
    disabled = models.BooleanField(null=True, default=False)
    ip_address = models.CharField(max_length=255, null=True, blank=True)
    port = models.IntegerField(null=True, blank=True)
    public_key = models.CharField(max_length=255, null=True, blank=True)
    private_key = models.CharField(max_length=255, null=True, blank=True)
    last_changed_datetime = models.DateTimeField(
        auto_now=True,
    )
    peer_groups = models.ManyToManyField(
        "PeerGroup", blank=True, through=PeerGroup.peers.through
    )

    def __str__(self):
        return f"{self.name} - {self.description}"

    def save(self, force_insert=False, force_update=False, **kwargs):
        sc = ServerConfiguration.objects.all()[0]
        if (not self.private_key) or (not self.public_key):
            public_key, private_key = generate_keys()
            self.public_key = public_key
            self.private_key = private_key
        if not self.port:
            self.port = sc.peer_default_port
        if not self.ip_address:
            peers = Peer.objects.all()
            sc_intf = ipaddress.ip_interface(sc.network_address)
            ip_address_pool = [x for x in sc_intf.network.hosts()]
            if peers:
                ip_addresses_to_exclude = [
                    ipaddress.ip_interface(p.ip_address).ip
                    for p in peers
                    if p.ip_address
                ]
                ip_address_pool = [
                    x for x in ip_address_pool if x not in ip_addresses_to_exclude
                ]
            self.ip_address = ip_address_pool[1]
        super().save(force_insert, force_update)


class Target(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, null=True, blank=True)
    disabled = models.BooleanField(null=True, default=False)
    ip_address = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        validators=[validator_is_valid_target_ip_address],
    )
    port = models.IntegerField(null=True, blank=True)
    allow_modify_self = models.BooleanField(null=True, default=True)
    allow_modify_peer_groups = models.BooleanField(null=True, default=True)
    last_changed_datetime = models.DateTimeField(
        auto_now=True,
    )
    peer_groups = models.ManyToManyField(
        "PeerGroup", blank=True, through=PeerGroup.targets.through
    )

    def __str__(self):
        return f"{self.name} - {self.description}"


class ServerConfiguration(models.Model):
    network_address = models.CharField(max_length=255, validators=[is_network_address])
    host_name_external = models.CharField(max_length=255, null=False, blank=False)
    port_external = models.IntegerField(null=False)
    port_internal = models.IntegerField(null=False)
    upstream_dns_ip_address = models.CharField(
        max_length=255, null=False, blank=False, validators=[validator_is_single_address]
    )
    local_networks = models.CharField(
        max_length=512, null=True, blank=True, validators=[validator_are_network_addresses]
    )
    wireguard_config_path = models.CharField(max_length=255)
    script_path_post_down = models.CharField(max_length=255)
    script_path_post_up = models.CharField(max_length=255)
    public_key = models.CharField(max_length=255, null=True, blank=True)
    private_key = models.CharField(max_length=255, null=True, blank=True)
    peer_default_port = models.IntegerField()
    last_changed_datetime = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return f"{self.host_name_external} - {self.port_external}"

    def save(self, force_insert=False, force_update=False, **kwargs):
        if (not self.private_key) or (not self.public_key):
            public_key, private_key = generate_keys()
            self.public_key = public_key
            self.private_key = private_key
        super().save(force_insert, force_update)
