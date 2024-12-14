# from ..db_seed import populate_dictionary_data
# migrations.RunPython(populate_dictionary_data),

from django.dispatch import receiver
from django.db.models.signals import post_migrate

from .common import IP_ADDRESS_INTERNET, PEER_GROUP_EVERYONE_NAME, TARGET_INTERNET_NAME
from .util import generate_keys, get_next_free_ip_address

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


@receiver(post_migrate)
def at_end_migrate(
    sender, app_config, verbosity, interactive, using, plan, apps, **kwargs
):
    PeerGroup = apps.get_model("api_app", "PeerGroup")
    peer_group_everyone_existing = PeerGroup.objects.filter(
        name=PEER_GROUP_EVERYONE_NAME
    )
    if not peer_group_everyone_existing:
        peer_group_everyone = PeerGroup(
            name=PEER_GROUP_EVERYONE_NAME,
            description="All peers in the system",
            allow_modify_self=False,
            allow_modify_peers=False,
            allow_modify_targets=True,
        )
        peer_group_everyone.save()

    Target = apps.get_model("api_app", "Target")
    target_internet_existing = Target.objects.filter(name=TARGET_INTERNET_NAME)
    if not target_internet_existing:
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
    server_configuration_existing = ServerConfiguration.objects.all()
    public_key, private_key = generate_keys()
    ip_address = get_next_free_ip_address(
        network_address=IP_ADDRESS_SERVER_DEFAULT,
        existing_ip_addresses=[],
        for_server=True,
    )
    server_configuration = (
        server_configuration_existing[0]
        if server_configuration_existing
        else ServerConfiguration(
            host_name_external=SERVER_FQDN_DEFAULT,
            network_address=IP_ADDRESS_SERVER_DEFAULT,
            ip_address=ip_address,
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
    )
    server_configuration.ip_address = ip_address
    if not server_configuration.public_key:
        server_configuration.public_key = public_key
    if not server_configuration.ip_address:
        server_configuration.private_key = private_key
    server_configuration.save()

    server_configuration = ServerConfiguration.objects.all()[0]
    Peer = apps.get_model("api_app", "Peer")
    peers_existing = Peer.objects.all()
    if not peers_existing:
        for peer_name, description in SAMPLE_PEERS:
            peer_existing = Peer.objects.filter(name=peer_name)
            if peer_existing:
                continue
            peers = Peer.objects.all()
            existing_ip_addresses = []
            if peers:
                existing_ip_addresses = (
                    [p.ip_address for p in peers if p.ip_address] if peers else []
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
