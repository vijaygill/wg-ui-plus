import { Routes } from '@angular/router';

import { AboutComponent } from './about/about.component';
import { HomeComponent } from './home/home.component';
import { PeergroupComponent } from './peergroup/peergroup.component';
import { TestpageComponent } from './testpage/testpage.component';

export const routes: Routes = [
    { path: 'home', component: HomeComponent },
    { path: 'about', component: AboutComponent },
    { path: 'peer-group', component: PeergroupComponent },
    { path: 'test-page', component: TestpageComponent },
    { path: '*', component: AboutComponent },
];
