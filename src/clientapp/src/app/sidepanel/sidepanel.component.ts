import { CommonModule } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule, RouterOutlet } from '@angular/router';
import { MenuItem } from 'primeng/api';
import { MenuModule } from 'primeng/menu';
import { AppSharedModule } from '../app-shared.module';
import { UserSessionInfo } from '../webapi.entities';
import { Subscription } from 'rxjs';
import { LoginService } from '../login-service';

@Component({
    standalone: true,
    selector: 'app-sidepanel',
    imports: [CommonModule, FormsModule, RouterModule, RouterOutlet, AppSharedModule, MenuModule],
    templateUrl: './sidepanel.component.html',
    styleUrl: './sidepanel.component.scss'
})
export class SidepanelComponent implements OnInit {
  items: MenuItem[] = [] as MenuItem[];
  itemsAuthorised: MenuItem[] = [
    {
      label: 'Server',
      expanded: true,
      items: [
        {
          label: 'Monitor Peers',
          route: '/server-monitor-peers',
        },
        {
          label: 'Monitor IP-Tables',
          route: '/server-monitor-iptables',
        },
        {
          label: 'VPN Layout',
          route: '/server-vpn-layout',
        },
        {
          label: 'Configuration',
          route: '/server-configuration',
        },
      ]
    },
    {
      separator: true
    },
    {
      label: 'Manage Data',
      items: [
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
      ]
    },
    {
      separator: true
    },
    {
      items: [
        {
          label: 'About',
          route: '/about',
        },
        {
          label: 'Log out',
          command: () => {
            this.loginService.logout();
          },
        }
      ]
    }
  ];

  itemsAnonymous: MenuItem[] = [
    {
      label: 'Server',
      expanded: true,
      items: [
        {
          label: 'Monitor Peers',
          route: '/server-monitor-peers',
        },
        {
          label: 'Monitor IP-Tables',
          route: '/server-monitor-iptables',
        },
        {
          label: 'VPN Layout',
          route: '/server-vpn-layout',
        },
      ]
    },
    {
      separator: true
    },
    {
      items: [
        {
          label: 'About',
          route: '/about',
        },
        {
          label: 'Log in',
          route: '/login',
        }
      ]
    }
  ];

  @Input() popup:boolean = false;

  userSessionInfo!: UserSessionInfo;
  loginServiceSubscription !: Subscription;

  constructor(private loginService: LoginService) { }

  ngOnInit(): void {
    this.loginServiceSubscription = this.loginService.getUserSessionInfo().subscribe(data => {
      this.userSessionInfo = data;
      this.items = this.userSessionInfo.is_logged_in ? this.itemsAuthorised : this.itemsAnonymous;
    });
    this.loginService.checkIsUserAuthenticated();
  }

  ngOnDestroy() {
    if (this.loginServiceSubscription) {
      this.loginServiceSubscription.unsubscribe();
    }
  }


}
