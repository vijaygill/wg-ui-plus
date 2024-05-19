# add following to your 0001_initial.py
# migrations.RunPython(populate_dictionary_data),

def populate_dictionary_data(apps, schema_editor):
    PeerGroup = apps.get_model('mainapp', 'PeerGroup')
    peer_group = PeerGroup(name = 'EveryOne', description = 'All peers in the system',
                           allow_modify_self = False,
                           allow_modify_peers = False,
                           allow_modify_targets = True,)
    peer_group.save()

    Target = apps.get_model('mainapp', 'Target')
    target = Target(name = 'Internet', description = 'Mmmmm....Internet....',
                    allow_modify_self = False,
                    allow_modify_peer_groups = True,)
    target.save()

    ServerConfiguration = apps.get_model('mainapp', 'ServerConfiguration')
    serverConfiguration = ServerConfiguration(host_name_external = 'myvpn.duckdns.org',
                    ip_address = '192.168.2.1/24',
                    port_external = 1196,
                    port_internal = '51820',
                    wireguard_config_path = '/config/wireguard/wg0.conf',
                    script_path_post_down = '/config/wireguard/scripts/post-up.sh',
                    script_path_post_up = '/config/wireguard/scripts/post-down.sh',
                    public_key = 'public key',
                    private_key = 'private key',
                    peer_default_port = 1196)
    serverConfiguration.save()
