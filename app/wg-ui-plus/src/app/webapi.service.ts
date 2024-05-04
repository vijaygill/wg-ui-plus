import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, of } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class WebapiService {

    private urlListPeerList = '/api/data/peers';
    private urlListIpTableChainList = '/api/data/iptablechains';

    private urlDockerContainerList = '/api/docker/container/list';
    private urlDockerContainerStart = '/api/docker/container/start';
    private urlDockerContainerStop = '/api/docker/container/stop';

    constructor(private http: HttpClient) {}

    getPeerList(): Observable<Peer[]> {
        return this.http.get<Peer[]>(this.urlListPeerList);
    }

    getIpTablesChainList(): Observable<IpTablesChain[]> {
        return this.http.get<IpTablesChain[]>(this.urlListIpTableChainList);
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

export interface Peer{
    id: number;
    name: string;
    device_name: string;
    is_vip: boolean;
    ip_address: string;
}


export interface IpTablesChain{
    id: number;
    name: string;
    description: string;
}

export interface DockerContainer{
    id: string;
    name: string;
    short_id: string;
    status: string;
}
