import { Routes } from '@angular/router';

import { AboutComponent } from './about/about.component';
import { HomeComponent } from './home/home.component';
import { TestpageComponent } from './testpage/testpage.component';
import { ManagePeersComponent } from './manage-peers/manage-peers.component';
import { ManagePeerGroupsComponent } from './manage-peer-groups/manage-peer-groups.component';
import { ManageTargetGroupsComponent } from './manage-target-groups/manage-target-groups.component';
import { ManageTargetsComponent } from './manage-targets/manage-targets.component';

export const routes: Routes = [
    { path: 'home', component: HomeComponent },
    { path: 'about', component: AboutComponent },
    { path: 'manage-peer-groups', component: ManagePeerGroupsComponent },
    { path: 'manage-peers', component: ManagePeersComponent },
    { path: 'manage-target-groups', component: ManageTargetGroupsComponent },
    { path: 'manage-targets', component: ManageTargetsComponent },
    { path: 'test-page', component: TestpageComponent },
    { path: '*', component: AboutComponent },
];
