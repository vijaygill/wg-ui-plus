import { Routes } from '@angular/router';

import { AboutComponent } from './pages/app-about/app-about.component';
import { HomeComponent } from './pages/home/home.component';
import { TestpageComponent } from './pages/testpage/testpage.component';
import { ManagePeersComponent } from './pages/manage-peers/manage-peers.component';
import { ManagePeerGroupsComponent } from './pages/manage-peer-groups/manage-peer-groups.component';
import { ManageTargetsComponent } from './pages/manage-targets/manage-targets.component';
import { ManageServerConfigurationComponent } from './pages/manage-server-configuration/manage-server-configuration.component';
import { LoginComponent } from './pages/login/login.component';
import { ServerVpnLayoutComponent } from './pages/server-vpn-layout/server-vpn-layout.component';
import { ServerMonitorIptablesComponent } from './pages/server-monitor-iptables/server-monitor-iptables.component';
import { ServerMonitorPeersComponent } from './pages/server-monitor-peers/server-monitor-peers.component';

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
