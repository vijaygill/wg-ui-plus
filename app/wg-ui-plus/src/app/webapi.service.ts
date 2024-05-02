import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, of } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class WebapiService {

    private peersUrl = 'http://orangepi5-plus:13080/peers';

    constructor(private http: HttpClient) {}

    getPeers(): Observable<Peer[]> {
        return this.http.get<Peer[]>(this.peersUrl);
    }

}

export interface Peer{
    id: number;
    name: string;
}


