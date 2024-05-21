import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { TreeNode } from 'primeng/api';
import { expand, map } from 'rxjs/operators'

@Injectable({
    providedIn: 'root'
})
export class WebapiService {

    private urlPeerGroup = '/api/v1/data/peer_group/';
    private urlPeer = '/api/v1/data/peer/';
    private urlTarget = '/api/v1/data/target/';
    private urlServerConfiguration = '/api/v1/data/server_configuration/';
    private urlGetWireguardConfiguration = '/api/v1/data/control/wireguard_get_configuration';
    private urlControlWireguardRestart = '/api/v1/control/wireguard_restart';
    private urlControlGenerateConfigurationFiles = '/api/v1/control/wireguard_generate_configuration_files';
    private urlPeerGroupHeirarchy = '/api/v1/data/target_heirarchy/'

    constructor(private http: HttpClient) { }

    getPeerGroupList(): Observable<PeerGroup[]> {
        return this.http.get<PeerGroup[]>(this.urlPeerGroup);
    }

    getPeerGroup(id: number): Observable<PeerGroup> {
        return this.http.get<PeerGroup>(this.urlPeerGroup + id);
    }

    savePeerGroup(item: PeerGroup): Observable<PeerGroup> {
        if (item) {
            item.peer_ids = item.peers ? item.peers.map(x => x.id) : [];
            item.target_ids = item.targets ? item.targets.map(x => x.id) : [];
        }
        var res = item.id
            ? this.http.put<PeerGroup>(this.urlPeerGroup + item.id + '/', item)
            : this.http.post<PeerGroup>(this.urlPeerGroup, item);
        return res;
    }

    getPeerList(): Observable<Peer[]> {
        return this.http.get<Peer[]>(this.urlPeer);
    }

    getPeer(id: number): Observable<Peer> {
        return this.http.get<Peer>(this.urlPeer + id + '/');
    }

    savePeer(item: Peer): Observable<Peer> {
        if (item) {
            item.peer_group_ids = item.peer_groups ? item.peer_groups.map(x => x.id) : [];
        }
        var res = item.id
            ? this.http.put<Peer>(this.urlPeer + item.id + '/', item)
            : this.http.post<Peer>(this.urlPeer, item);
        return res;
    }

    getTargetList(): Observable<Target[]> {
        return this.http.get<Target[]>(this.urlTarget);
    }

    getTarget(id: number): Observable<Target> {
        return this.http.get<Target>(this.urlTarget + id + '/');
    }

    saveTarget(item: Target): Observable<Target> {
        if (item) {
            item.peer_group_ids = item.peer_groups ? item.peer_groups.map(x => x.id) : [];
        }
        var res = item.id
            ? this.http.put<Target>(this.urlTarget + item.id + '/', item)
            : this.http.post<Target>(this.urlTarget, item);
        return res;
    }

    getServerConfigurationList(): Observable<ServerConfiguration[]> {
        return this.http.get<ServerConfiguration[]>(this.urlServerConfiguration);
    }

    getServerConfiguration(id: number): Observable<ServerConfiguration> {
        return this.http.get<ServerConfiguration>(this.urlServerConfiguration + id);
    }

    saveServerConfiguration(item: ServerConfiguration): Observable<ServerConfiguration> {
        var res = item.id
            ? this.http.put<ServerConfiguration>(this.urlServerConfiguration + item.id + '/', item)
            : this.http.post<ServerConfiguration>(this.urlServerConfiguration, item);
        return res;
    }

    getWireguardConfiguration(): Observable<WireguardConfiguration> {
        return this.http.get<WireguardConfiguration>(this.urlGetWireguardConfiguration);
    }

    generateConfigurationFiles(): Observable<any> {
        return this.http.get<any>(this.urlControlGenerateConfigurationFiles);
    }

    wireguardRestart(): Observable<any> {
        return this.http.get<any>(this.urlControlWireguardRestart);
    }

    getTargetHeirarchy(): Observable<TreeNode[]> {
        return this.http.get<Target[]>(this.urlPeerGroupHeirarchy)
            .pipe(map(targets => {
                let items = targets.map(target => {
                    return {
                        label: target.name,
                        expanded: true,
                        data: {
                            details: target.ip_address,
                        },
                        children: target.peer_groups.map(peer_group => {
                            return {
                                label: peer_group.name,
                                expanded: true,
                                data: {
                                    details: '',
                                },
                                children: peer_group.peers.map(peer => {
                                    return {
                                        label: peer.name,
                                        expanded: true,
                                        data: {
                                            details: peer.ip_address,
                                        },
                                    } as TreeNode
                                })
                            } as TreeNode
                        })
                    } as TreeNode
                }
                );
                let parentItem = {
                    label: 'VPN',
                    expanded: true,
                    data: {
                        details: 'VPN running on your server',
                    },
                    children: items,
                } as TreeNode;
                let res = [parentItem];
                return res;
            }));
    }
}

export interface Entity {
    id: number;
}

export interface Peer extends Entity {
    name: string;
    description: string;
    ip_address: string;
    port: number;
    disabled: boolean;
    public_key: string;
    private_key: string;
    peer_configuration: string;
    peer_groups: PeerGroup[];
    peer_groups_lookup: PeerGroup[];
    peer_group_ids: number[];
    qr: string;
    target_names: string;
}

export interface PeerGroup extends Entity {
    name: string;
    description: string;
    disabled: boolean;
    allow_modify_self: boolean;
    allow_modify_peers: boolean;
    allow_modify_targets: boolean;
    targets: Target[];
    targets_lookup: Target[];
    peers: Peer[];
    peers_lookup: Peer[];
    peer_ids: number[];
    target_ids: number[];
    target_names: string;
    is_everyone_group: boolean;
}

export interface Target extends Entity {
    name: string;
    description: string;
    ip_address: string;
    disabled: boolean;
    allow_modify_self: boolean;
    allow_modify_peer_groups: boolean;
    peer_groups: PeerGroup[];
    peer_groups_lookup: PeerGroup[];
    peer_group_ids: number[];
}

export interface ServerConfiguration {
    id: number;
    network_address: string;
    host_name_external: string;
    port_internal: number;
    port_external: number;
    wireguard_config_path: string;
    script_path_post_down: string;
    script_path_post_up: string;
    public_key: string;
    private_key: string;
    peer_default_port: number;
    upstream_dns_ip_address: string;
}

export interface WireguardConfiguration {
    server_configuration: string;
    peer_configurations: string[];
}


export interface ServerValidationError {
    type: string;
    errors: ServerValidationErrorItem[];
}

export interface ServerValidationErrorItem {
    code: string;
    detail: string;
    attr: string;
}

