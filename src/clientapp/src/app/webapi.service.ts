import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, Subject, of } from 'rxjs';
import { TreeNode } from 'primeng/api';
import { map, tap } from 'rxjs/operators'
import { ChangeUserPasswordInfo, ConnectedPeerInformation, IpTablesLog, LicenseInfo, Peer, PeerGroup, ServerConfiguration, ServerStatus, Target, UserCrendentials, UserSessionInfo, WireguardConfiguration } from './webapi.entities';

@Injectable({
    providedIn: 'root'
})
export class WebapiService {

    private urlGetLicense = '/api/v1/license';
    private urlPeerGroup = '/api/v1/data/peer_group/';
    private urlPeer = '/api/v1/data/peer/';
    private urlTarget = '/api/v1/data/target/';
    private urlServerConfiguration = '/api/v1/data/server_configuration/';
    private urlGetWireguardConfiguration = '/api/v1/data/control/wireguard_get_configuration';
    private urlControlWireguardRestart = '/api/v1/control/wireguard_restart';
    private urlControlGenerateConfigurationFiles = '/api/v1/control/wireguard_generate_configuration_files';
    private urlPeerGroupHeirarchy = '/api/v1/data/target_heirarchy/';
    private urlGetConnectedPeers = '/api/v1/control/wireguard_get_connected_peers';
    private urlGetIpTablesLog = '/api/v1/control/get_iptables_log';
    private urlGetServerStatus = '/api/v1/control/get_server_status';
    private urlIsUserLogIn = '/api/v1/auth/login';
    private urlIsUserLogOut = '/api/v1/auth/logout';
    private urlChangeUserPassword = '/api/v1/auth/change_password';

    constructor(private http: HttpClient) { }

    getLicense(): Observable<LicenseInfo> {
        return this.http.get<LicenseInfo>(this.urlGetLicense);
    }

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

        res = res.pipe(tap(() => {
            this.checkServerStatus();
        }));
        return res;
    }

    deletePeerGroup(item: PeerGroup): Observable<PeerGroup> {
        var res = this.http.delete<PeerGroup>(this.urlPeerGroup + item.id + '/');
        res = res.pipe(tap(() => {
            this.checkServerStatus();
        }));
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
        res = res.pipe(tap(() => {
            this.checkServerStatus();
        }));
        return res;
    }

    deletePeer(item: Peer): Observable<Peer> {
        var res = this.http.delete<Peer>(this.urlPeer + item.id + '/');
        res = res.pipe(tap(() => {
            this.checkServerStatus();
        }));
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
        res = res.pipe(tap(() => {
            this.checkServerStatus();
        }));
        return res;
    }

    deleteTarget(item: Target): Observable<Target> {
        var res = this.http.delete<Target>(this.urlTarget + item.id + '/');
        res = res.pipe(tap(() => {
            this.checkServerStatus();
        }));
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
        res = res.pipe(tap(() => {
            this.checkServerStatus();
        }));
        return res;
    }

    getWireguardConfiguration(): Observable<WireguardConfiguration> {
        return this.http.get<WireguardConfiguration>(this.urlGetWireguardConfiguration)
            .pipe(tap(() => {
                this.checkServerStatus();
            }));
    }

    generateConfigurationFiles(): Observable<any> {
        return this.http.get<any>(this.urlControlGenerateConfigurationFiles)
            .pipe(tap(() => {
                this.checkServerStatus();
            }));
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
                        type: 'target',
                        expanded: true,
                        data: {
                            disabled: target.disabled,
                            details: target.description,
                            ip_address: target.ip_address,
                        },
                        children: target.peer_groups.map(peer_group => {
                            return {
                                label: peer_group.name,
                                expanded: true,
                                type: 'peerGroup',
                                data: {
                                    disabled: peer_group.disabled,
                                    details: peer_group.description,
                                },
                                children: peer_group.peers.map(peer => {
                                    return {
                                        label: peer.name,
                                        expanded: true,
                                        type: 'peer',
                                        data: {
                                            disabled: peer.disabled,
                                            details: peer.description,
                                            ip_address: peer.ip_address,
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

    getConnectedPeers(): Observable<ConnectedPeerInformation> {
        return this.http.get<ConnectedPeerInformation>(this.urlGetConnectedPeers);
    }

    getIpTablesLog(): Observable<IpTablesLog> {
        return this.http.get<IpTablesLog>(this.urlGetIpTablesLog);
    }

    serverStatus: Subject<ServerStatus> = new Subject<ServerStatus>();

    checkServerStatus(): void {
        this.http.get<ServerStatus>(this.urlGetServerStatus).subscribe(data => {
            this.serverStatus.next(data);
        });
    }

    checkIsUserAuthenticated(): Observable<UserSessionInfo> {
        return this.http.get<UserSessionInfo>(this.urlIsUserLogIn);
    }

    login(credentials: UserCrendentials): Observable<UserSessionInfo> {
        return this.http.post<UserSessionInfo>(this.urlIsUserLogIn, credentials);
    }

    logout(): Observable<UserSessionInfo> {
        return this.http.get<UserSessionInfo>(this.urlIsUserLogOut);
    }

    changeUserPassword(info: ChangeUserPasswordInfo): Observable<UserSessionInfo> {
        return this.http.post<UserSessionInfo>(this.urlChangeUserPassword, info);
    }

}
