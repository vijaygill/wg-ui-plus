# from ..db_seed import populate_dictionary_data
# migrations.RunPython(populate_dictionary_data),


IP_ADDRESS_INTERNET = '0.0.0.0/0'
IP_ADDRESS_SERVER_DEFAULT = '192.168.2.0/24'
SERVER_FQDN_DEFAULT = 'myvpn.duckdns.org'
PORT_DEFAULT_EXTERNAL = 1196
PORT_DEFAULT_INTERNAL = '51820'
PORT_DEFAULT_PEER = PORT_DEFAULT_EXTERNAL
UPSTREAM_DNS_SERVER_DEFAULT = '192.168.0.5'

def populate_dictionary_data(apps, schema_editor):
    PeerGroup = apps.get_model('api_app', 'PeerGroup')
    peer_group = PeerGroup(name = 'EveryOne', description = 'All peers in the system',
                           allow_modify_self = False,
                           allow_modify_peers = False,
                           allow_modify_targets = True,)
    peer_group.save()

    Target = apps.get_model('api_app', 'Target')
    peer_group_everyone = PeerGroup.objects.all()[0]
    target = Target(name = 'Internet', description = 'Internet - We all need it.',
                    ip_address = IP_ADDRESS_INTERNET,
                    allow_modify_self = False,
                    allow_modify_peer_groups = True,)
    target.save()
    target.peer_groups.add(peer_group_everyone)
    peer_group_everyone.targets.add(target)
    target.save()

    ServerConfiguration = apps.get_model('api_app', 'ServerConfiguration')
    serverConfiguration = ServerConfiguration(host_name_external = SERVER_FQDN_DEFAULT,
                    network_address = IP_ADDRESS_SERVER_DEFAULT,
                    port_external = PORT_DEFAULT_EXTERNAL,
                    port_internal = PORT_DEFAULT_INTERNAL,
                    wireguard_config_path = '/config/wireguard/wg0.conf',
                    script_path_post_up = '/config/wireguard/scripts/post-up.sh',
                    script_path_post_down = '/config/wireguard/scripts/post-down.sh',
                    peer_default_port = PORT_DEFAULT_PEER,
                    upstream_dns_ip_address = UPSTREAM_DNS_SERVER_DEFAULT)
    serverConfiguration.save()
