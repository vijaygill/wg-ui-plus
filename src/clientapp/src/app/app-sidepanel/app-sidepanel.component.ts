
import { Component, Input, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AppSharedModule } from '../app-shared.module';
import { NavMenuItem } from '../nav-menu-item';
import { UserSessionInfo } from '../webapi.entities';
import { Subscription } from 'rxjs';
import { LoginService } from '../login-service';

/**
 * Navigation item: a NavMenuItem plus the optional bits the side panel needs
 * (tooltip text, a click command for items such as "Log out" that perform an
 * action instead of navigating, and `replaceUrl` for router links such as
 * "Log in" that should not leave a back-navigation entry behind).
 */
export interface SidepanelMenuItem extends NavMenuItem {
    tooltip: string;
    command?: () => void;
    replaceUrl?: boolean;
}

/**
 * A labelled group of navigation items (rendered as a subheader in the nav
 * list and flattened with dividers in the popup menu).
 */
export interface SidepanelMenuSection {
    label?: string;
    items: SidepanelMenuItem[];
}

@Component({
  standalone: true,
  selector: 'app-sidepanel',
  imports: [FormsModule, RouterModule, AppSharedModule],
  templateUrl: './app-sidepanel.component.html',
  styleUrl: './app-sidepanel.component.scss'
})
export class SidepanelComponent implements OnInit {
  private menuItemMonitorPeers: SidepanelMenuItem = {
    label: 'Monitor Peers',
    route: '/server-monitor-peers',
    icon: 'visibility',
    tooltip: 'See the status of all the peers in one page.',
  };
  private menuItemMonitorIPTables: SidepanelMenuItem = {
    label: 'Monitor IP-Tables',
    route: '/server-monitor-iptables',
    icon: 'visibility',
    tooltip: 'See the chains defined in IPTables.',
  };
  private menuItemVPNLayout: SidepanelMenuItem = {
    label: 'VPN Layout',
    route: '/server-vpn-layout',
    icon: 'grid_view',
    tooltip: 'See the how all peers/peer-groups/targets tie together.',
  };
  private menuItemServerConfiguration: SidepanelMenuItem = {
    label: 'Configuration',
    route: '/server-configuration',
    icon: 'build',
    tooltip: 'Configure the VPN on the server side.',
  };
  private menuItemAbout: SidepanelMenuItem = {
    label: 'About',
    route: '/about',
    icon: 'help',
    tooltip: 'Some information about the application itself.',
  };
  private menuItemLogIn: SidepanelMenuItem = {
    label: 'Log in',
    route: '/login',
    icon: 'login',
    tooltip: 'Log in to manage the data (peers/peer-groups/targets).',
    replaceUrl: true,
  };
  private menuItemLogOut: SidepanelMenuItem = {
    label: 'Log out',
    icon: 'logout',
    tooltip: 'Log out (before you step away from your machine).',
    command: () => {
      this.loginService.logout();
    },
  };
  private menuItemPeerGroups: SidepanelMenuItem = {
    label: 'Peer-Groups',
    route: '/manage-peer-groups',
    icon: 'account_tree',
    tooltip: 'Add/Edit/Remove Peer-Groups. Link/Unlink Peer-Groups with Targets.',
  };
  private menuItemPeers: SidepanelMenuItem = {
    label: 'Peers',
    route: '/manage-peers',
    icon: 'desktop_windows',
    tooltip: 'Add/Edit/Remove Peers. Add/Remove Peers to Peer-Groups.',
  };
  private menuItemTargets: SidepanelMenuItem = {
    label: 'Targets',
    route: '/manage-targets',
    icon: 'track_changes',
    tooltip: 'Add/Edit/Remove Targets. Link/Unlink Targets with Peer-Groups.',
  };

  sections: SidepanelMenuSection[] = [];

  itemsAuthorized: SidepanelMenuSection[] = [
    {
      label: 'Server',
      items: [
        this.menuItemMonitorPeers,
        this.menuItemMonitorIPTables,
        this.menuItemVPNLayout,
        this.menuItemServerConfiguration,
      ]
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
      items: [
        this.menuItemAbout,
        this.menuItemLogOut,
      ]
    }
  ];

  itemsAnonymous: SidepanelMenuSection[] = [
    {
      label: 'Server',
      items: [
        this.menuItemMonitorPeers,
        this.menuItemMonitorIPTables,
        this.menuItemVPNLayout,
      ]
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
      this.sections = this.userSessionInfo.is_logged_in ? this.itemsAuthorized : this.itemsAnonymous;
    });
    this.loginService.checkIsUserAuthenticated();
  }

  ngOnDestroy() {
    if (this.loginServiceSubscription) {
      this.loginServiceSubscription.unsubscribe();
    }
  }

  onItemCommand(item: SidepanelMenuItem): void {
    if (item.command) {
      item.command();
    }
  }
}
