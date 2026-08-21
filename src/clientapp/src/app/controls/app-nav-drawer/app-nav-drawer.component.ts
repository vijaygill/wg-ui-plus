import { Component, Input, ChangeDetectionStrategy, computed } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { AppSharedModule } from '../../app-shared.module';
import { NavMenuItem } from '../../nav-menu-item';
import { LoginService } from '../../services/login.service';

/**
 * Navigation item: a NavMenuItem plus the optional bits the navigation drawer
 * needs (tooltip text, a click command for items such as "Log out" that perform
 * an action instead of navigating, and `replaceUrl` for router links such as
 * "Log in" that should not leave a back-navigation entry behind).
 */
export interface NavDrawerMenuItem extends NavMenuItem {
    tooltip: string;
    command?: () => void;
    replaceUrl?: boolean;
}

/** A labelled group of navigation items (rendered as a subheader in the nav list). */
export interface NavDrawerMenuSection {
    label?: string;
    items: NavDrawerMenuItem[];
}

/**
 * Side navigation drawer rendered inside the app's `mat-sidenav`.
 *
 * Supports a collapsible icon-only rail: when `collapsed` is true the item
 * labels and section headers are hidden and full labels are revealed via
 * hover tooltips. The authentication item (Log in / Log out) is pinned at the
 * bottom of the drawer.
 */
@Component({
  standalone: true,
  selector: 'app-nav-drawer',
  imports: [FormsModule, RouterModule, AppSharedModule],
  templateUrl: './app-nav-drawer.component.html',
  styleUrl: './app-nav-drawer.component.scss',
  // Exposes the collapsed state as a host class so the icon-only rail's
  // Material list-item internals can be styled globally (see styles.scss).
  changeDetection: ChangeDetectionStrategy.Eager,
  host: { '[class.nav-drawer-collapsed]': 'collapsed' },
})
export class NavDrawerComponent {
  private menuItemMonitorPeers: NavDrawerMenuItem = {
    label: 'Monitor Peers',
    route: '/server-monitor-peers',
    icon: 'visibility',
    tooltip: 'See the status of all the peers in one page.',
  };
  private menuItemMonitorIPTables: NavDrawerMenuItem = {
    label: 'Monitor IP-Tables',
    route: '/server-monitor-iptables',
    icon: 'visibility',
    tooltip: 'See the chains defined in IPTables.',
  };
  private menuItemVPNLayout: NavDrawerMenuItem = {
    label: 'VPN Layout',
    route: '/server-vpn-layout',
    icon: 'grid_view',
    tooltip: 'See how all peers/peer-groups/targets tie together.',
  };
  private menuItemServerConfiguration: NavDrawerMenuItem = {
    label: 'Configuration',
    route: '/server-configuration',
    icon: 'build',
    tooltip: 'Configure the VPN on the server side.',
  };
  private menuItemAbout: NavDrawerMenuItem = {
    label: 'About',
    route: '/about',
    icon: 'help',
    tooltip: 'Some information about the application itself.',
  };
  private menuItemLogIn: NavDrawerMenuItem = {
    label: 'Log in',
    route: '/login',
    icon: 'login',
    tooltip: 'Log in to manage the data (peers/peer-groups/targets).',
    replaceUrl: true,
  };
  private menuItemLogOut: NavDrawerMenuItem = {
    label: 'Log out',
    icon: 'logout',
    tooltip: 'Log out (before you step away from your machine).',
    command: () => {
      this.loginService.logout();
    },
  };
  private menuItemPeerGroups: NavDrawerMenuItem = {
    label: 'Peer-Groups',
    route: '/manage-peer-groups',
    icon: 'account_tree',
    tooltip: 'Add/Edit/Remove Peer-Groups. Link/Unlink Peer-Groups with Targets.',
  };
  private menuItemPeers: NavDrawerMenuItem = {
    label: 'Peers',
    route: '/manage-peers',
    icon: 'desktop_windows',
    tooltip: 'Add/Edit/Remove Peers. Add/Remove Peers to Peer-Groups.',
  };
  private menuItemTargets: NavDrawerMenuItem = {
    label: 'Targets',
    route: '/manage-targets',
    icon: 'track_changes',
    tooltip: 'Add/Edit/Remove Targets. Link/Unlink Targets with Peer-Groups.',
  };

  private readonly isLoggedIn = computed(() => this.loginService.userSessionInfo().is_logged_in);

  /** Sections rendered in the upper portion of the drawer. */
  readonly sections = computed<NavDrawerMenuSection[]>(() =>
    this.isLoggedIn() ? this.itemsAuthorized : this.itemsAnonymous);

  /** Items pinned at the bottom of the drawer (About + auth item). */
  readonly bottomItems = computed<NavDrawerMenuItem[]>(() =>
    this.isLoggedIn() ? this.bottomAuthorized : this.bottomAnonymous);

  private itemsAuthorized: NavDrawerMenuSection[] = [
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
  ];

  private bottomAuthorized: NavDrawerMenuItem[] = [
    this.menuItemAbout,
    this.menuItemLogOut,
  ];

  private itemsAnonymous: NavDrawerMenuSection[] = [
    {
      label: 'Server',
      items: [
        this.menuItemMonitorPeers,
        this.menuItemMonitorIPTables,
        this.menuItemVPNLayout,
      ]
    },
  ];

  private bottomAnonymous: NavDrawerMenuItem[] = [
    this.menuItemAbout,
    this.menuItemLogIn,
  ];

  /** When true, the drawer renders as an icon-only rail. */
  @Input() collapsed: boolean = false;

  constructor(private loginService: LoginService) {
    this.loginService.checkIsUserAuthenticated();
  }

  onItemCommand(item: NavDrawerMenuItem): void {
    if (item.command) {
      item.command();
    }
  }
}
