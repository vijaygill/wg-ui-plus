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
  imports: [CommonModule, FormsModule, RouterModule, AppSharedModule, MenuModule],
  templateUrl: './sidepanel.component.html',
  styleUrl: './sidepanel.component.scss'
})
export class SidepanelComponent implements OnInit {
  private menuItemMonitorPeers = {
    label: 'Monitor Peers',
    route: '/server-monitor-peers',
    icon: 'pi pi-eye',
  } as MenuItem;
  private menuItemMonitorIPTables = {
    label: 'Monitor IP-Tables',
    route: '/server-monitor-iptables',
    icon: 'pi pi-eye',
  } as MenuItem;
  private menuItemVPNLayout = {
    label: 'VPN Layout',
    route: '/server-vpn-layout',
    icon: 'pi pi-th-large',
  } as MenuItem;
  private menuItemServerConfiguration = {
    label: 'Configuration',
    route: '/server-configuration',
    icon: 'pi pi-wrench',
  } as MenuItem;
  private menuItemAbout = {
    label: 'About',
    route: '/about',
    icon: 'pi pi-question',
  } as MenuItem;
  private menuItemLogIn = {
    label: 'Log in',
    route: '/login',
    icon: 'pi pi-sign-in',
  } as MenuItem;
  private menuItemLogOut = {
    label: 'Log out',
    command: () => {
      this.loginService.logout();
    },
    icon: 'pi pi-sign-out',
  } as MenuItem;

  private menuItemPeerGroups = {
    label: 'Peer-Groups',
    route: '/manage-peer-groups',
    icon: 'pi pi-sitemap',
  } as MenuItem;
  private menuItemPeers = {
    label: 'Peers',
    route: '/manage-peers',
    icon: 'pi pi-desktop',
  } as MenuItem;
  private menuItemTargets = {
    label: 'Targets',
    route: '/manage-targets',
    icon: 'pi pi-bullseye',
  } as MenuItem;


  items: MenuItem[] = [] as MenuItem[];
  itemsAuthorised: MenuItem[] = [
    {
      label: 'Server',
      expanded: true,
      items: [
        this.menuItemMonitorPeers,
        this.menuItemMonitorIPTables,
        this.menuItemVPNLayout,
        this.menuItemServerConfiguration,
      ]
    },
    {
      separator: true
    },
    {
      label: 'Manage Data',
      items: [
        this.menuItemPeerGroups,
        this.menuItemPeers,
        this.menuItemTargets,
      ]
    },
    {
      separator: true
    },
    {
      items: [
        this.menuItemAbout,
        this.menuItemLogOut,
      ]
    }
  ];

  itemsAnonymous: MenuItem[] = [
    {
      label: 'Server',
      expanded: true,
      items: [
        this.menuItemMonitorPeers,
        this.menuItemMonitorIPTables,
        this.menuItemVPNLayout,
      ]
    },
    {
      separator: true
    },
    {
      items: [
        this.menuItemAbout,
        this.menuItemLogIn,
      ]
    }
  ];

  @Input() popup: boolean = false;

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
