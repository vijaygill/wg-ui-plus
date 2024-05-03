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
}

export interface Peer{
    id: number;
    name: string;
    device_name: string;
    is_vip: boolean;
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
