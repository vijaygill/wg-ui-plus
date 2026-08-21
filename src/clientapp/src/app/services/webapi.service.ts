import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map, tap } from 'rxjs/operators'
import { ChangeUserPasswordInfo, ConnectedPeerInformation, EmailConfiguration, IpTablesLog, LicenseInfo, McpConfiguration, OrgChartNode, Peer, PeerGroup, ServerConfiguration, ServerStatus, Target, UserCredentials, UserSessionInfo, WireguardConfiguration } from '../webapi.entities';

/** Status exposed before the first server response arrives. */
const INITIAL_SERVER_STATUS = {
    need_regenerate_files: false,
    application_details: { current_version: '', latest_live_version: '' },
} as ServerStatus;

@Injectable({
    providedIn: 'root'
})
export class WebapiService {

    private urlGetLicense = '/api/v1/license';
    private urlPeerGroup = '/api/v1/data/peer_group/';
    private urlPeer = '/api/v1/data/peer/';
    private urlPeerSendEmail = '/api/v1/data/peer/send_peer_email';
    private urlSendTestEmail = '/api/v1/control/send_test_email';
    private urlTarget = '/api/v1/data/target/';
    private urlServerConfiguration = '/api/v1/data/server_configuration/';
    private urlGetWireguardConfiguration = '/api/v1/data/control/wireguard_get_configuration';
    private urlControlWireguardRestart = '/api/v1/control/wireguard_restart';
    private urlControlGenerateConfigurationFiles = '/api/v1/control/wireguard_generate_configuration_files';
    private urlPeerGroupHierarchy = '/api/v1/data/target_heirarchy/';
    private urlGetConnectedPeers = '/api/v1/control/wireguard_get_connected_peers';
    private urlGetIpTablesLog = '/api/v1/control/get_iptables_log';
    private urlGetServerStatus = '/api/v1/control/get_server_status';
    private urlIsUserLogIn = '/api/v1/auth/login';
    private urlIsUserLogOut = '/api/v1/auth/logout';
    private urlChangeUserPassword = '/api/v1/auth/change_password';
    private urlMcpConfiguration = '/api/v1/control/mcp/configuration';
    private urlMcpToken = '/api/v1/control/mcp/token';
    private urlEmailConfiguration = '/api/v1/control/email/configuration';
    private urlEmailConnectivity = '/api/v1/control/email/test_connectivity';

    /** Latest known server status; signal writes schedule change detection. */
    private serverStatusSignal = signal<ServerStatus>(INITIAL_SERVER_STATUS);

    /** Read-only view of the latest server status (never undefined). */
    readonly serverStatus = this.serverStatusSignal.asReadonly();

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

    sendConfigurationByEmail(item: Peer): Observable<any> {
        var res = this.http.post<any>(this.urlPeerSendEmail, { peer_id: item.id });
        res = res.pipe(tap(() => {
            this.checkServerStatus();
        }));
        return res;
    }

    sendTestEmail(): Observable<{ message: string }> {
        return this.http.post<{ message: string }>(this.urlSendTestEmail, {});
    }

    testEmailConnectivity(): Observable<{ message: string }> {
        return this.http.post<{ message: string }>(this.urlEmailConnectivity, {});
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

    getMcpConfiguration(): Observable<McpConfiguration> { return this.http.get<McpConfiguration>(this.urlMcpConfiguration); }
    updateMcpConfiguration(enabled: boolean): Observable<McpConfiguration> { return this.http.patch<McpConfiguration>(this.urlMcpConfiguration, { mcp_enabled: enabled }); }
    generateMcpToken(): Observable<McpConfiguration> { return this.http.post<McpConfiguration>(this.urlMcpToken, {}); }
    copyMcpToken(): Observable<{ mcp_token: string }> { return this.http.get<{ mcp_token: string }>(this.urlMcpToken); }

    getEmailConfiguration(): Observable<EmailConfiguration> { return this.http.get<EmailConfiguration>(this.urlEmailConfiguration); }
    updateEmailConfiguration(item: EmailConfiguration): Observable<EmailConfiguration> { return this.http.patch<EmailConfiguration>(this.urlEmailConfiguration, item); }

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

    getTargetHierarchy(): Observable<OrgChartNode[]> {
        return this.http.get<Target[]>(this.urlPeerGroupHierarchy)
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
                                    } as OrgChartNode
                                })
                            } as OrgChartNode
                        })
                    } as OrgChartNode
                }
                );
                let parentItem = {
                    label: 'VPN',
                    expanded: true,
                    data: {
                        details: 'VPN running on your server',
                    },
                    children: items,
                } as OrgChartNode;
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

    checkServerStatus(): void {
        this.http.get<ServerStatus>(this.urlGetServerStatus).subscribe(data => {
            this.serverStatusSignal.set(data);
        });
    }

    pushServerStatus(serverStatus: ServerStatus): void {
        this.serverStatusSignal.set(serverStatus);
    }

    checkIsUserAuthenticated(): Observable<UserSessionInfo> {
        return this.http.get<UserSessionInfo>(this.urlIsUserLogIn);
    }

    login(credentials: UserCredentials): Observable<UserSessionInfo> {
        return this.http.post<UserSessionInfo>(this.urlIsUserLogIn, credentials);
    }

    logout(): Observable<UserSessionInfo> {
        return this.http.get<UserSessionInfo>(this.urlIsUserLogOut);
    }

    changeUserPassword(info: ChangeUserPasswordInfo): Observable<UserSessionInfo> {
        return this.http.post<UserSessionInfo>(this.urlChangeUserPassword, info);
    }

}
