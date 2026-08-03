import { Component, OnInit, OnDestroy } from '@angular/core';
import { Router, RouterModule, RouterOutlet, NavigationEnd } from '@angular/router';
import { MatDrawerMode } from '@angular/material/sidenav';
import { NavDrawerComponent } from './app-nav-drawer/app-nav-drawer.component';
import { AppSharedModule } from './app-shared.module';
import { PlatformInformation, ServerStatus, UserSessionInfo } from './webapi.entities';
import { Subscription, filter } from 'rxjs';
import { WebapiService } from './webapi.service';
import { LoginService } from './login.service';
import { PlatformInformationService } from './platform-information.service';
import { PeriodicRefreshUiService } from './periodic-refresh-ui.service';
import { NotificationService } from './notification.service';
import { NotificationComponent } from './notification/notification.component';
import { ThemeService } from './theme.service';

@Component({
    standalone: true,
    selector: 'app-root',
    imports: [RouterModule, RouterOutlet, NavDrawerComponent, AppSharedModule, NotificationComponent],
    templateUrl: './app.component.html',
    styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'WireGuard UI Plus';

  serverStatus: ServerStatus = {
    need_regenerate_files: false,
    application_details: { current_version: '', latest_live_version: '', },
  } as ServerStatus;
  userSessionInfo: UserSessionInfo = { is_logged_in: false, message: '' };

  platformInformation: PlatformInformation = {} as PlatformInformation;

  /** Desktop only: whether the navigation drawer is collapsed to an icon rail. */
  navCollapsed = false;

  /** Small screen only: whether the overlay drawer is open. */
  mobileNavOpen = false;

  timerSubscription !: Subscription;
  serverStatusSubscription !: Subscription;
  loginServiceSubscription !: Subscription;
  platformInformationServiceSubscription !: Subscription;
  routerSubscription !: Subscription;

  /** Key of the status-derived banner currently shown, to avoid re-pushing on every poll. */
  lastStatusBannerKey: string | null = null;

  constructor(private notification: NotificationService,
    private webapiService: WebapiService,
    private loginService: LoginService,
    private platformInformationService: PlatformInformationService,
    private periodicRefreshUiService: PeriodicRefreshUiService,
    private themeService: ThemeService,
    private router: Router) { }

  ngOnInit() {
    this.platformInformationServiceSubscription = this.platformInformationService.platformInformation.subscribe(
      (data) => {
        this.platformInformation = data;
      }
    );

    this.timerSubscription = this.periodicRefreshUiService.onTimer.subscribe(val => {
      this.webapiService.checkServerStatus();
    });

    this.serverStatusSubscription = this.webapiService.serverStatus.subscribe(data => {
      this.serverStatus = data;
      this.syncStatusBanner();
    });

    this.loginServiceSubscription = this.loginService.getUserSessionInfo().subscribe(data => {
      this.userSessionInfo = data;
      this.syncStatusBanner();
    });
    this.loginService.checkIsUserAuthenticated();
    this.webapiService.checkServerStatus();
    this.platformInformationService.checkPlatform();

    // Auto-close the overlay drawer after navigating on small screens.
    this.routerSubscription = this.router.events
      .pipe(filter((event) => event instanceof NavigationEnd))
      .subscribe(() => {
        this.mobileNavOpen = false;
      });
  }

  ngOnDestroy() {
    if (this.timerSubscription) {
      this.timerSubscription.unsubscribe();
    }
    if (this.serverStatusSubscription) {
      this.serverStatusSubscription.unsubscribe();
    }
    if (this.loginServiceSubscription) {
      this.loginServiceSubscription.unsubscribe();
    }
    if (this.platformInformationServiceSubscription) {
      this.platformInformationServiceSubscription.unsubscribe();
    }
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }

  get isSmallScreen(): boolean {
    return this.platformInformation.is_small_screen;
  }

  /** Persistent drawer on desktop, overlay drawer on small screens. */
  get drawerMode(): MatDrawerMode {
    return this.isSmallScreen ? 'over' : 'side';
  }

  get sidenavOpened(): boolean {
    return this.isSmallScreen ? this.mobileNavOpen : true;
  }

  get navDrawerCollapsed(): boolean {
    // Collapse-to-rail only applies to the persistent (desktop) drawer.
    return !this.isSmallScreen && this.navCollapsed;
  }

  /** Server status dot colour class. */
  get statusClass(): string {
    const status = this.serverStatus?.status;
    if (status === 'error') {
      return 'status-error';
    }
    if (status === 'warning' || status === 'warn') {
      return 'status-warn';
    }
    return 'status-ok';
  }

  /** Human-readable label for the server status orb. */
  get statusLabel(): string {
    const status = this.serverStatus?.status;
    if (status === 'error') {
      return 'Offline';
    }
    if (status === 'warning' || status === 'warn') {
      return 'Warning';
    }
    return 'Online';
  }

  get theme() {
    return this.themeService.theme;
  }

  onToggleNav(): void {
    if (this.isSmallScreen) {
      this.mobileNavOpen = !this.mobileNavOpen;
    } else {
      this.navCollapsed = !this.navCollapsed;
    }
  }

  /** Accessible label for the nav toggle, describing the action the tap performs. */
  get navToggleLabel(): string {
    // Tapping always toggles: on small screens it opens/closes the overlay
    // drawer; on desktop it collapses/expands the persistent rail. The label
    // reflects what that tap does — "Collapse" when the surface is currently
    // open/expanded, "Expand" when it is closed/collapsed.
    const collapsesOnTap = this.isSmallScreen
      ? this.mobileNavOpen          // drawer open → tapping closes it
      : !this.navCollapsed;         // rail expanded → tapping collapses it
    return collapsesOnTap ? 'Collapse navigation' : 'Expand navigation';
  }

  toggleTheme(): void {
    this.themeService.toggle();
  }

  /** Which status-driven banner (if any) should be showing right now. */
  private computeStatusBannerKey(): string | null {
    if (this.serverStatus?.status === 'error') {
      return 'error';
    }
    if (this.serverStatus?.need_regenerate_files && this.userSessionInfo.is_logged_in) {
      return 'warn:regenerate';
    }
    return null;
  }

  /** Keeps the unified banner in sync with the server status (offline / regenerate). */
  private syncStatusBanner(): void {
    const key = this.computeStatusBannerKey();
    if (key === this.lastStatusBannerKey) {
      return;
    }
    this.lastStatusBannerKey = key;
    if (key === null) {
      this.notification.clear();
      return;
    }
    if (key === 'error') {
      this.notification.show({
        type: 'error',
        message: this.serverStatus?.message || 'Connection to the server was lost.',
        persistent: true,
      });
    } else if (key === 'warn:regenerate') {
      this.notification.show({
        type: 'warn',
        message: 'This will regenerate Server Configuration files and restart WireGuard.',
        action: { label: 'Apply Changes', callback: () => this.applyConfiguration() },
        persistent: true,
      });
    }
  }

  applyConfiguration(): void {
    this.webapiService.generateConfigurationFiles().subscribe(data => {
      this.notification.success('Configuration files generated on server.');
      this.webapiService.wireguardRestart().subscribe(() => {
        this.webapiService.checkServerStatus();
        this.notification.success('Wireguard restarted on server.');
      });
    });
  }


}
