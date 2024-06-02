import { Routes } from '@angular/router';

import { AboutComponent } from './about/about.component';
import { HomeComponent } from './home/home.component';
import { TestpageComponent } from './testpage/testpage.component';
import { ManagePeersComponent } from './manage-peers/manage-peers.component';
import { ManagePeerGroupsComponent } from './manage-peer-groups/manage-peer-groups.component';
import { ManageTargetsComponent } from './manage-targets/manage-targets.component';
import { ManageServerConfigurationComponent } from './manage-server-configuration/manage-server-configuration.component';
import { LoginComponent } from './login/login.component';

export const routes: Routes = [
    { path: '', component: LoginComponent },
    { path: 'home', component: HomeComponent },
    { path: 'about', component: AboutComponent },
    { path: 'manage-peer-groups', component: ManagePeerGroupsComponent },
    { path: 'manage-peers', component: ManagePeersComponent },
    { path: 'manage-targets', component: ManageTargetsComponent },
    { path: 'manage-server-configuration', component: ManageServerConfigurationComponent },
    { path: 'test-page', component: TestpageComponent },
    { path: '*', component: LoginComponent },
];
