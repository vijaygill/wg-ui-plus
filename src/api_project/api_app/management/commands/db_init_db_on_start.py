#!/usr/bin/python
import os
import datetime
import traceback

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User

from api_app.util import generate_keys, get_next_free_ip_address
from api_app.common import (
    DEFAULT_ADMIN_USER_NAME,
    DEFAULT_ADMIN_USER_PASSWORD,
    IP_ADDRESS_INTERNET,
    PEER_GROUP_EVERYONE_NAME,
    SCRIPT_PATH_POST_DOWN,
    SCRIPT_PATH_POST_UP,
    TARGET_INTERNET_NAME,
    TRUE_VALUES,
    WIREGUARD_CONFIG_PATH,
)
from api_app.models import Peer, PeerGroup, ServerConfiguration, Target

IP_ADDRESS_SERVER_DEFAULT = "192.168.2.0/24"
SERVER_FQDN_DEFAULT = "myvpn.duckdns.org"
PORT_DEFAULT_EXTERNAL = 1196
PORT_DEFAULT_INTERNAL = "51820"
PORT_DEFAULT_PEER = PORT_DEFAULT_EXTERNAL
UPSTREAM_DNS_SERVER_DEFAULT = "192.168.0.5"
SAMPLE_PEERS = [
    ("Mobile phone", "Your mobile phone"),
    ("Laptop", "May need access to VPN occasionally"),
]


class Command(BaseCommand):
    help = "Seeds some data if not present already."

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        try:
            self.init_admin_user()
            self.init_server_config()
            self.init_peer_groups()
            self.init_targets()

            server_configuration = ServerConfiguration.objects.all()[0]
            peers_existing = Peer.objects.all()
            if peers_existing:
                self.stdout.write(
                    self.style.SUCCESS("Peers exist. No need to create sample peers.")
                )
            else:
                for peer_name, description in SAMPLE_PEERS:
                    peer_existing = Peer.objects.filter(name=peer_name)
                    if peer_existing:
                        continue
                    peers = Peer.objects.all()
                    existing_ip_addresses = []
                    if peers:
                        existing_ip_addresses = (
                            [p.ip_address for p in peers if p.ip_address]
                            if peers
                            else []
                        )
                        existing_ip_addresses += [server_configuration.ip_address]
                    existing_ip_addresses = [ip for ip in existing_ip_addresses if ip]
                    ip_address = get_next_free_ip_address(
                        network_address=server_configuration.network_address,
                        existing_ip_addresses=existing_ip_addresses,
                    )
                    public_key, private_key = generate_keys()
                    peer = Peer(
                        name=peer_name,
                        description=description,
                        public_key=public_key,
                        private_key=private_key,
                        ip_address=ip_address,
                    )
                    peer.save()
            self.stdout.write(self.style.SUCCESS("DB-seed initialised successfully."))
        except Exception as e:
            raise CommandError("Error:" + traceback.format_exception(e))

    def init_admin_user(self, *args, **options):
        try:
            user = User.objects.filter(username=DEFAULT_ADMIN_USER_NAME)
            if user:
                user = user[0]
            if not user:
                user = User.objects.create_user(
                    DEFAULT_ADMIN_USER_NAME, "", DEFAULT_ADMIN_USER_PASSWORD
                )
                user.save()
                self.stdout.write(
                    self.style.SUCCESS("Admin user initialised successfully.")
                )
            else:
                self.stdout.write(self.style.SUCCESS("Admin user exists already."))
        except Exception as e:
            raise CommandError("Error:" + traceback.format_exception(e))

    def init_server_config(self):
        try:
            server_config = ServerConfiguration.objects.all()
            if server_config:
                server_config = server_config[0]
                if not server_config.ip_address:
                    server_config.save()
                self.stdout.write(
                    self.style.SUCCESS("ServerConfiguration exists. No need to create.")
                )
            if not server_config:
                server_config = ServerConfiguration(
                    host_name_external=SERVER_FQDN_DEFAULT,
                    network_address=IP_ADDRESS_SERVER_DEFAULT,
                    port_external=PORT_DEFAULT_EXTERNAL,
                    port_internal=PORT_DEFAULT_INTERNAL,
                    wireguard_config_path=WIREGUARD_CONFIG_PATH,
                    script_path_post_up=SCRIPT_PATH_POST_UP,
                    script_path_post_down=SCRIPT_PATH_POST_DOWN,
                    peer_default_port=PORT_DEFAULT_PEER,
                    upstream_dns_ip_address=UPSTREAM_DNS_SERVER_DEFAULT,
                    last_changed_datetime=datetime.datetime.now(datetime.timezone.utc),
                )
                server_config.save()
                self.stdout.write(self.style.SUCCESS("Created Server Configuration"))

            scs = ServerConfiguration.objects.all()
            for sc in scs:
                is_dirty = False
                network_address = os.environ.get("WG_NETWORK_ADDRESS", None)
                if network_address and sc.network_address != network_address:
                    sc.network_address = network_address
                    is_dirty = True
                    self.stdout.write(self.style.SUCCESS("Updated network_address"))
                host_name_external = os.environ.get("WG_HOST_NAME_EXTERNAL", None)
                if host_name_external and sc.host_name_external != host_name_external:
                    sc.host_name_external = host_name_external
                    is_dirty = True
                    self.stdout.write(self.style.SUCCESS("Updated host_name_external"))
                local_networks = os.environ.get("WG_LOCAL_NETWORKS", None)
                if local_networks and (sc.local_networks != local_networks):
                    sc.local_networks = local_networks
                    is_dirty = True
                    self.stdout.write(self.style.SUCCESS("Updated local_networks"))
                upstream_dns_ip_address = os.environ.get("WG_UPSTREAM_DNS_SERVER", None)
                if (
                    upstream_dns_ip_address
                    and sc.upstream_dns_ip_address != upstream_dns_ip_address
                ):
                    sc.upstream_dns_ip_address = upstream_dns_ip_address
                    is_dirty = True
                    self.stdout.write(
                        self.style.SUCCESS("Updated upstream_dns_ip_address")
                    )
                port_external = os.environ.get("WG_PORT_EXTERNAL", None)
                if port_external and sc.port_external != port_external:
                    sc.port_external = port_external
                    is_dirty = True
                    self.stdout.write(self.style.SUCCESS("Updated port_external"))
                port_internal = os.environ.get("WG_PORT_INTERNAL", None)
                if port_internal and sc.port_internal != port_internal:
                    sc.port_internal = port_internal
                    is_dirty = True
                    self.stdout.write(self.style.SUCCESS("Updated port_internal"))
                strict_allowed_ips_in_peer_config = os.environ.get("WG_STRICT_ALLOWED_IPS_IN_PEER_CONFIG", '').lower() in TRUE_VALUES
                if sc.strict_allowed_ips_in_peer_config != strict_allowed_ips_in_peer_config:
                    sc.strict_allowed_ips_in_peer_config = strict_allowed_ips_in_peer_config
                    is_dirty = True
                    self.stdout.write(self.style.SUCCESS("Updated strict_allowed_ips_in_peer_config"))

                if is_dirty:
                    sc.save()
                    self.stdout.write(
                        self.style.SUCCESS("Updated Server Configuration")
                    )
        except Exception as e:
            raise CommandError("Error:" + traceback.format_exception(e))

    def init_peer_groups(self):
        peer_group_everyone_existing = PeerGroup.objects.filter(
            name=PEER_GROUP_EVERYONE_NAME
        )
        if peer_group_everyone_existing:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Peer-Group {PEER_GROUP_EVERYONE_NAME} exists. No need to create."
                )
            )
        else:
            peer_group_everyone = PeerGroup(
                name=PEER_GROUP_EVERYONE_NAME,
                description="All peers in the system",
                allow_modify_self=False,
                allow_modify_peers=False,
                allow_modify_targets=True,
            )
            peer_group_everyone.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Peer-Group {PEER_GROUP_EVERYONE_NAME} created."
                )
            )

    def init_targets(self):
        target_internet_existing = Target.objects.filter(name=TARGET_INTERNET_NAME)
        if target_internet_existing:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Target {TARGET_INTERNET_NAME} exists. No need to create."
                )
            )
        else:
            peer_group_everyone = PeerGroup.objects.get(
                name=PEER_GROUP_EVERYONE_NAME
            )
            target = Target(
                name=TARGET_INTERNET_NAME,
                description=f"{TARGET_INTERNET_NAME} - We all need it.",
                ip_address=IP_ADDRESS_INTERNET,
                allow_modify_self=False,
                allow_modify_peer_groups=True,
            )
            target.save()
            target.peer_groups.add(peer_group_everyone)
            peer_group_everyone.targets.add(target)
            target.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Target {TARGET_INTERNET_NAME} created."
                )
            )
