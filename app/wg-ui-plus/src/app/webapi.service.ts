import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, of } from 'rxjs';

@Injectable({
    providedIn: 'root'
})
export class WebapiService {

    private urlPeerGroupList = '/api/data/peer_group';
    private urlPeerGroupSave = '/api/data/peer_group';

    private urlPeerList = '/api/data/peer';
    private urlPeerSave = '/api/data/peer';

    private urlTargetList = '/api/data/target';
    private urlTargetSave = '/api/data/target';

    private urlServerConfigurationList = '/api/data/server_configuration';
    private urlServerConfigurationSave = '/api/data/server_configuration';

    private urlGetWireguardConfiguration = '/api/data/wireguard_configuration';

    private urlControlWireguardRestart = '/api/control/wireguard_restart';
    private urlControlGenerateConfigurationFiles = '/api/control/generate_configuration_files';

    private urlDockerContainerList = '/api/docker/container/list';
    private urlDockerContainerStart = '/api/docker/container/start';
    private urlDockerContainerStop = '/api/docker/container/stop';

    constructor(private http: HttpClient) { }

    getPeerGroupList(): Observable<PeerGroup[]> {
        return this.http.get<PeerGroup[]>(this.urlPeerGroupList);
    }

    getPeerGroup(id: number): Observable<PeerGroup> {
        return this.http.get<PeerGroup>(this.urlPeerGroupList + '/' + id);
    }

    savePeerGroup(item: PeerGroup): Observable<PeerGroup> {
        return this.http.post<PeerGroup>(this.urlPeerGroupSave, item);
    }

    getPeerList(): Observable<Peer[]> {
        return this.http.get<Peer[]>(this.urlPeerList);
    }

    getPeer(id: number): Observable<Peer> {
        return this.http.get<Peer>(this.urlPeerList + '/' + id);
    }

    savePeer(item: Peer): Observable<Peer> {
        return this.http.post<Peer>(this.urlPeerSave, item);
    }

    getTargetList(): Observable<Target[]> {
        return this.http.get<Target[]>(this.urlTargetList);
    }

    getTarget(id: number): Observable<Target> {
        return this.http.get<Target>(this.urlTargetList + '/' + id);
    }

    saveTarget(item: Target): Observable<Target> {
        return this.http.post<Target>(this.urlTargetSave, item);
    }

    getServerConfigurationList(): Observable<ServerConfiguration[]> {
        return this.http.get<ServerConfiguration[]>(this.urlServerConfigurationList);
    }

    getServerConfiguration(id: number): Observable<ServerConfiguration> {
        return this.http.get<ServerConfiguration>(this.urlServerConfigurationList + '/' + id);
    }

    saveServerConfiguration(item: ServerConfiguration): Observable<ServerConfiguration> {
        return this.http.post<ServerConfiguration>(this.urlServerConfigurationSave, item);
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

    getDockerContainerList(): Observable<DockerContainer[]> {
        return this.http.get<DockerContainer[]>(this.urlDockerContainerList);
    }

    startDockerContainer(name: string): Observable<DockerContainer[]> {
        return this.http.get<DockerContainer[]>(this.urlDockerContainerStart + '?name=' + name);
    }

    stopDockerContainer(name: string): Observable<DockerContainer[]> {
        return this.http.get<DockerContainer[]>(this.urlDockerContainerStop + '?name=' + name);
    }
}

export interface Peer {
    id: number;
    name: string;
    ip_address: string;
    port: number;
    disabled: boolean;
    public_key: string;
    private_key: string;
    peer_configuration: string;
    peer_group_peer_links: PeerGroupPeerLink[];
    lookup_peer_groups: PeerGroupPeerLink[];
}

export interface PeerGroup {
    id: number;
    name: string;
    description: string;
    disabled: boolean;
    allow_modify_self: boolean;
    allow_modify_peers: boolean;
    allow_modify_targets: boolean;
    peer_group_peer_links: PeerGroupPeerLink[];
    lookup_peers: PeerGroupPeerLink[];
    peer_group_target_links: PeerGroupTargetLink[];
    lookup_targets: PeerGroupTargetLink[];
}

export interface PeerGroupPeerLink {
    id: number;
    peer_group_id: number;
    peer_group: PeerGroup;
    peer_id: number;
    peer: Peer;
}

export interface Target {
    id: number;
    name: string;
    description: string;
    ip_address: string;
    disabled: boolean;
    allow_modify_self: boolean;
    peer_group_target_links: PeerGroupTargetLink[];
    lookup_peergroups: PeerGroupTargetLink[];
}

export interface PeerGroupTargetLink {
    id: number;
    peer_group_id: number;
    peer_group: PeerGroup;
    target_id: number;
    target: Target;
}

export interface DockerContainer {
    id: string;
    name: string;
    short_id: string;
    status: string;
}

export interface ServerConfiguration {
    id: number;
    ip_address: string;
    host_name_external: string;
    port_internal: number;
    port_external: number;
    wireguard_config_path: string;
    script_path_post_down: string;
    script_path_post_up: string;
    public_key: string;
    private_key: string;
    peer_default_port: number;
}

export interface WireguardConfiguration {
    server_configuration: string;
    peer_configurations: string[];
}