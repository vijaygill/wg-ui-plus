import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule, RouterOutlet } from '@angular/router';
import { MenuItem, Message } from 'primeng/api';
import { MenuModule } from 'primeng/menu';
import { AppSharedModule } from '../app-shared.module';
import { routes } from '../app.routes';
import { ServerStatus, UserSessionInfo } from '../webapi.entities';
import { Subscription, interval } from 'rxjs';
import { LoginService } from '../loginService';
import { WebapiService } from '../webapi.service';


@Component({
  selector: 'app-sidepanel',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, RouterOutlet, AppSharedModule, MenuModule],
  templateUrl: './sidepanel.component.html',
  styleUrl: './sidepanel.component.scss'
})
export class SidepanelComponent implements OnInit {
  items: MenuItem[] = [] as MenuItem[];
  itemsDefault: MenuItem[] = [
    {
      items: [
        {
          label: 'Home',
          route: '/home',
        },
        {
          label: 'Peer-Groups',
          route: '/manage-peer-groups',
        },
        {
          label: 'Peers',
          route: '/manage-peers',
        },
        {
          label: 'Targets',
          route: '/manage-targets',
        },
        {
          label: 'Server',
          route: '/manage-server-configuration',
        },
        // {
        //   label: 'Test',
        //   route: '/test-page',
        // },
        {
          label: 'About',
          route: '/about',
        },
      ]
    }
  ];

  itemsLogin: MenuItem[] = [
    {
      items: [
        {
          label: 'Home',
          route: '/home',
        },
        {
          label: 'About',
          route: '/about',
        },
        {
          label: 'Log in',
          route: '/login',
        },
      ]
    }
  ];


  itemsLogout: MenuItem[] = [{
    items: [{
      label: 'Log out',
      command: () => {
        this.loginService.logout();
      },
    }]
  }];

  userSessionInfo!: UserSessionInfo;
  loginServiceSubscription !: Subscription;

  constructor(private loginService: LoginService) { }

  ngOnInit(): void {
    this.loginServiceSubscription = this.loginService.getUserSessionInfo().subscribe(data => {
      this.userSessionInfo = data;
      this.items = this.userSessionInfo.is_logged_in ? [...this.itemsDefault, ...this.itemsLogout] : this.itemsLogin;
    });
    this.loginService.checkIsUserAuthenticated();
  }

  ngOnDestroy() {
    if (this.loginServiceSubscription) {
      this.loginServiceSubscription.unsubscribe();
    }
  }

  
}
