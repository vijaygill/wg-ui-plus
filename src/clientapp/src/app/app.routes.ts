import { Routes } from '@angular/router';

import { AboutComponent } from './about/about.component';
import { HomeComponent } from './home/home.component';
import { TestpageComponent } from './testpage/testpage.component';
import { ManagePeersComponent } from './manage-peers/manage-peers.component';
import { ManagePeerGroupsComponent } from './manage-peer-groups/manage-peer-groups.component';
import { ManageTargetsComponent } from './manage-targets/manage-targets.component';
import { ManageServerConfigurationComponent } from './manage-server-configuration/manage-server-configuration.component';
import { LoginComponent } from './login/login.component';
import { ServerVpnLayoutComponent } from './server-vpn-layout/server-vpn-layout.component';
import { ServerMonitorIptablesComponent } from './server-monitor-iptables/server-monitor-iptables.component';
import { ServerMonitorPeersComponent } from './server-monitor-peers/server-monitor-peers.component';

export const routes: Routes = [
    { path: '', redirectTo: 'server-monitor-peers', pathMatch: 'full' },
    { path: 'home', component: HomeComponent },
    { path: 'login', component: LoginComponent },
    { path: 'logout', component: LoginComponent },
    { path: 'about', component: AboutComponent },
    { path: 'manage-peer-groups', component: ManagePeerGroupsComponent },
    { path: 'manage-peers', component: ManagePeersComponent },
    { path: 'manage-targets', component: ManageTargetsComponent },
    { path: 'server-configuration', component: ManageServerConfigurationComponent },
    { path: 'server-monitor-peers', component: ServerMonitorPeersComponent },
    { path: 'server-vpn-layout', component: ServerVpnLayoutComponent },
    { path: 'server-monitor-iptables', component: ServerMonitorIptablesComponent },
    { path: 'test-page', component: TestpageComponent },
    { path: '**', redirectTo: 'login', pathMatch: 'full' },
];
