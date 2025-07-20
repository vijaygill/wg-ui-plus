
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
  imports: [FormsModule, RouterModule, AppSharedModule, MenuModule],
  templateUrl: './sidepanel.component.html',
  styleUrl: './sidepanel.component.scss'
})
export class SidepanelComponent implements OnInit {
  private menuItemMonitorPeers = {
    label: 'Monitor Peers',
    route: '/server-monitor-peers',
    icon: 'pi pi-eye',
    tooltip: 'See the status of all the peers in one page.',
    tooltipPosition: 'top',
  } as MenuItem;
  private menuItemMonitorIPTables = {
    label: 'Monitor IP-Tables',
    route: '/server-monitor-iptables',
    icon: 'pi pi-eye',
    tooltip: 'See the chains defined in IPTables.',
  } as MenuItem;
  private menuItemVPNLayout = {
    label: 'VPN Layout',
    route: '/server-vpn-layout',
    icon: 'pi pi-th-large',
    tooltip: 'See the how all peers/peer-groups/targets tie together.',
  } as MenuItem;
  private menuItemServerConfiguration = {
    label: 'Configuration',
    route: '/server-configuration',
    icon: 'pi pi-wrench',
    tooltip: 'Configure the VPN on the server side.',
  } as MenuItem;
  private menuItemAbout = {
    label: 'About',
    route: '/about',
    icon: 'pi pi-question',
    tooltip: 'Some information about the application itself.',
  } as MenuItem;
  private menuItemLogIn = {
    label: 'Log in',
    route: '/login',
    icon: 'pi pi-sign-in',
    tooltip: 'Log in to manage the data (peers/peer-groups/targets).',
    replaceUrl: true,
  } as MenuItem;
  private menuItemLogOut = {
    label: 'Log out',
    command: () => {
      this.loginService.logout();
    },
    icon: 'pi pi-sign-out',
    tooltip: 'Log out (before you step away from your machine).',
    replaceUrl: true,
  } as MenuItem;

  private menuItemPeerGroups = {
    label: 'Peer-Groups',
    route: '/manage-peer-groups',
    icon: 'pi pi-sitemap',
    tooltip: 'Add/Edit/Remove Peer-Groups. Link/Unlink Peer-Groups with Targets.',
  } as MenuItem;
  private menuItemPeers = {
    label: 'Peers',
    route: '/manage-peers',
    icon: 'pi pi-desktop',
    tooltip: 'Add/Edit/Remove Peers. Add/Remove Peers to Peer-Groups.',
  } as MenuItem;
  private menuItemTargets = {
    label: 'Targets',
    route: '/manage-targets',
    icon: 'pi pi-bullseye',
    tooltip: 'Add/Edit/Remove Targets. Link/Unlink Targets with Peer-Groups.',
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
