# from ..db_seed import populate_dictionary_data
# migrations.RunPython(populate_dictionary_data),

import ipaddress

from .common import (IP_ADDRESS_INTERNET, PEER_GROUP_EVERYONE_NAME,
                     TARGET_INTERNET_NAME)
from .wireguardhelper import generate_keys

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


def populate_dictionary_data(apps, schema_editor):
    PeerGroup = apps.get_model("api_app", "PeerGroup")
    peer_group = PeerGroup(
        name=PEER_GROUP_EVERYONE_NAME,
        description="All peers in the system",
        allow_modify_self=False,
        allow_modify_peers=False,
        allow_modify_targets=True,
    )
    peer_group.save()

    Target = apps.get_model("api_app", "Target")
    peer_group_everyone = PeerGroup.objects.get(name=PEER_GROUP_EVERYONE_NAME)
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

    ServerConfiguration = apps.get_model("api_app", "ServerConfiguration")
    public_key, private_key = generate_keys()
    server_configuration = ServerConfiguration(
        host_name_external=SERVER_FQDN_DEFAULT,
        network_address=IP_ADDRESS_SERVER_DEFAULT,
        port_external=PORT_DEFAULT_EXTERNAL,
        port_internal=PORT_DEFAULT_INTERNAL,
        wireguard_config_path="/config/wireguard/wg0.conf",
        script_path_post_up="/config/wireguard/scripts/post-up.sh",
        script_path_post_down="/config/wireguard/scripts/post-down.sh",
        peer_default_port=PORT_DEFAULT_PEER,
        upstream_dns_ip_address=UPSTREAM_DNS_SERVER_DEFAULT,
        public_key=public_key,
        private_key=private_key,
    )
    server_configuration.save()

    server_configuration = ServerConfiguration.objects.all()[0]
    Peer = apps.get_model("api_app", "Peer")
    for peer_name, description in SAMPLE_PEERS:
        peers = Peer.objects.all()
        sc_intf = ipaddress.ip_interface(server_configuration.network_address)
        ip_address_pool = [x for x in sc_intf.network.hosts()]
        if peers:
            ip_addresses_to_exclude = [
                ipaddress.ip_interface(p.ip_address).ip for p in peers if p.ip_address
            ]
            ip_address_pool = [
                x for x in ip_address_pool if x not in ip_addresses_to_exclude
            ]
        ip_address = ip_address_pool[1]
        public_key, private_key = generate_keys()
        peer = Peer(
            name=peer_name,
            description=description,
            public_key=public_key,
            private_key=private_key,
            ip_address=ip_address,
        )
        peer.save()
