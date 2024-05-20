import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { PercentPipe } from '@angular/common';

@Injectable({
    providedIn: 'root'
})
export class WebapiService {

    private urlPeerGroupList = '/api/v1/peer_group';
    private urlPeerGroupSave = '/api/v1/peer_group/';

    private urlPeerList = '/api/v1/peer/';
    private urlPeerSave = '/api/v1/peer/';

    private urlTargetList = '/api/v1/target';
    private urlTargetSave = '/api/v1/target/';

    private urlServerConfigurationList = '/api/v1/server_configuration';
    private urlServerConfigurationSave = '/api/v1/server_configuration/';

    private urlGetWireguardConfiguration = '/api/v1/wireguard_configuration';

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
        var res = item.id == 0
            ? this.http.post<PeerGroup>(this.urlPeerGroupSave, item)
            : this.http.post<PeerGroup>(this.urlPeerGroupSave + item.id + '/', item);
        return res;
    }

    getPeerList(): Observable<Peer[]> {
        return this.http.get<Peer[]>(this.urlPeerList);
    }

    getPeer(id: number): Observable<Peer> {
        return this.http.get<Peer>(this.urlPeerList + '/' + id + '/');
    }

    savePeer(item: Peer): Observable<Peer> {
        var res = item.id
            ? this.http.put<Peer>(this.urlPeerSave + item.id + '/', item)
            : this.http.post<Peer>(this.urlPeerList, item);
        return res;
    }

    getTargetList(): Observable<Target[]> {
        return this.http.get<Target[]>(this.urlTargetList);
    }

    getTarget(id: number): Observable<Target> {
        return this.http.get<Target>(this.urlTargetList + id + '/');
    }

    saveTarget(item: Target): Observable<Target> {
        var res = item.id == 0
            ? this.http.post<Target>(this.urlTargetSave, item)
            : this.http.post<Target>(this.urlTargetSave + item.id + '/', item);
        return res;
    }

    getServerConfigurationList(): Observable<ServerConfiguration[]> {
        return this.http.get<ServerConfiguration[]>(this.urlServerConfigurationList);
    }

    getServerConfiguration(id: number): Observable<ServerConfiguration> {
        return this.http.get<ServerConfiguration>(this.urlServerConfigurationList + '/' + id);
    }

    saveServerConfiguration(item: ServerConfiguration): Observable<ServerConfiguration> {
        var res = item.id == 0
            ? this.http.post<ServerConfiguration>(this.urlServerConfigurationSave, item)
            : this.http.put<ServerConfiguration>(this.urlServerConfigurationSave + item.id + '/', item);
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
    description: string;
    ip_address: string;
    port: number;
    disabled: boolean;
    public_key: string;
    private_key: string;
    peer_configuration: string;
    peer_groups: PeerGroup[];
    peer_groups_lookup: PeerGroup[];
}

export interface PeerGroup {
    id: number;
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
}

export interface Target {
    id: number;
    name: string;
    description: string;
    ip_address: string;
    disabled: boolean;
    allow_modify_self: boolean;
    allow_modify_peer_groups: boolean;
    peer_groups: PeerGroup[];
    peer_groups_lookup: PeerGroup[];
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


export interface ServerValidationError {
    type: string;
    errors: ServerValidationErrorItem[];
}

export interface ServerValidationErrorItem {
    code: string;
    detail: string;
    attr: string;
}