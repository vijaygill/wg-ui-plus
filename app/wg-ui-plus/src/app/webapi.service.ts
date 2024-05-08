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

    private urlTargetGroupList = '/api/data/target_group';
    private urlTargetGroupSave = '/api/data/target_group';

    private urlTargetList = '/api/data/target';
    private urlTargetSave = '/api/data/target';

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

    getTargetGroupList(): Observable<TargetGroup[]> {
        return this.http.get<TargetGroup[]>(this.urlTargetGroupList);
    }

    getTargetGroup(id: number): Observable<TargetGroup> {
        return this.http.get<TargetGroup>(this.urlTargetGroupList + '/' + id);
    }

    saveTargetGroup(item: TargetGroup): Observable<TargetGroup> {
        return this.http.post<TargetGroup>(this.urlTargetGroupSave, item);
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
    device_name: string;
    ip_address: string;
    disabled: boolean;
}

export interface PeerGroup {
    id: number;
    name: string;
    description: string;
    disabled: boolean;
    is_inbuilt: boolean;
}

export interface TargetGroup {
    id: number;
    name: string;
    description: string;
    disabled: boolean;
    is_inbuilt: boolean;
}

export interface Target {
    id: number;
    name: string;
    description: string;
    ip_network: string;
    disabled: boolean;
    is_inbuilt: boolean;
}

export interface DockerContainer {
    id: string;
    name: string;
    short_id: string;
    status: string;
}
