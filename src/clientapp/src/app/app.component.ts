import { Component, OnInit, OnDestroy, ViewChild, ChangeDetectionStrategy, effect, signal } from '@angular/core';
import { Router, RouterModule, RouterOutlet, NavigationEnd } from '@angular/router';
import { MatDrawerMode, MatSidenavContainer } from '@angular/material/sidenav';
import { NavDrawerComponent } from './controls/app-nav-drawer/app-nav-drawer.component';
import { AppSharedModule } from './app-shared.module';
import { Subscription, filter } from 'rxjs';
import { WebapiService } from './services/webapi.service';
import { LoginService } from './services/login.service';
import { PlatformInformationService } from './services/platform-information.service';
import { PeriodicRefreshUiService } from './services/periodic-refresh-ui.service';
import { NotificationService } from './services/notification.service';
import { NotificationComponent } from './controls/notification/notification.component';
import { ThemeService } from './services/theme.service';

@Component({
    standalone: true,
    selector: 'app-root',
    imports: [RouterModule, RouterOutlet, NavDrawerComponent, AppSharedModule, NotificationComponent],
    templateUrl: './app.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit, OnDestroy {
  title = 'WireGuard UI Plus';

  /** Desktop only: whether the navigation drawer is collapsed to an icon rail. */
  navCollapsed = signal(false);

  /** Small screen only: whether the overlay drawer is open. */
  mobileNavOpen = signal(false);

  /** Reactive view of the latest server status from WebapiService, for the template. */
  readonly serverStatus = this.webapiService.serverStatus;

  /** The sidenav container, so the content margin can be re-synced on collapse. */
  @ViewChild(MatSidenavContainer) sidenavContainer?: MatSidenavContainer;

  timerSubscription !: Subscription;
  routerSubscription !: Subscription;

  /** Key of the status-derived banner currently shown, to avoid re-pushing on every poll. */
  lastStatusBannerKey: string | null = null;

  /**
   * Keeps the unified banner in sync with the server-status and session
   * signals (offline / regenerate). Replaces the previous subscriptions'
   * syncStatusBanner() calls; runs whenever either tracked signal changes.
   */
  private readonly statusBannerSync = effect(() => {
    this.syncStatusBanner();
  });

  constructor(private notification: NotificationService,
    private webapiService: WebapiService,
    private loginService: LoginService,
    private platformInformationService: PlatformInformationService,
    private periodicRefreshUiService: PeriodicRefreshUiService,
    private themeService: ThemeService,
    private router: Router) { }

  ngOnInit() {
    this.timerSubscription = this.periodicRefreshUiService.onTimer.subscribe(val => {
      this.webapiService.checkServerStatus();
    });

    this.loginService.checkIsUserAuthenticated();
    this.webapiService.checkServerStatus();
    this.platformInformationService.checkPlatform();

    // Auto-close the overlay drawer after navigating on small screens.
    this.routerSubscription = this.router.events
      .pipe(filter((event) => event instanceof NavigationEnd))
      .subscribe(() => {
        this.mobileNavOpen.set(false);
      });
  }

  ngOnDestroy() {
    if (this.timerSubscription) {
      this.timerSubscription.unsubscribe();
    }
    if (this.routerSubscription) {
      this.routerSubscription.unsubscribe();
    }
  }

  get isSmallScreen(): boolean {
    return this.platformInformationService.platformInformation().is_small_screen;
  }

  /** Persistent drawer on desktop, overlay drawer on small screens. */
  get drawerMode(): MatDrawerMode {
    return this.isSmallScreen ? 'over' : 'side';
  }

  get sidenavOpened(): boolean {
    return this.isSmallScreen ? this.mobileNavOpen() : true;
  }

  get navDrawerCollapsed(): boolean {
    // Collapse-to-rail only applies to the persistent (desktop) drawer.
    return !this.isSmallScreen && this.navCollapsed();
  }

  /** Server status dot colour class. */
  get statusClass(): string {
    const status = this.webapiService.serverStatus().status;
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
    const status = this.webapiService.serverStatus().status;
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
      this.mobileNavOpen.update(open => !open);
    } else {
      this.navCollapsed.update(collapsed => !collapsed);
      this.syncSidenavMargins();
    }
  }

  /**
   * Keeps the main content area in lock-step with the collapsing rail.
   *
   * The drawer width is transitioned in CSS (see app.component.scss), but
   * Angular Material only recomputes the content margin on drawer open/close.
   * Calling updateContentMargins() every frame during the transition makes the
   * main area's margin track the drawer element's current offsetWidth.
   */
  private syncSidenavMargins(): void {
    const container = this.sidenavContainer;
    if (!container) {
      return;
    }
    const start = performance.now();
    const duration = 400; // must match the width transition in app.component.scss
    const tick = () => {
      container.updateContentMargins();
      if (performance.now() - start < duration) {
        requestAnimationFrame(tick);
      }
    };
    requestAnimationFrame(tick);
  }

  /** Accessible label for the nav toggle, describing the action the tap performs. */
  get navToggleLabel(): string {
    // Tapping always toggles: on small screens it opens/closes the overlay
    // drawer; on desktop it collapses/expands the persistent rail. The label
    // reflects what that tap does — "Collapse" when the surface is currently
    // open/expanded, "Expand" when it is closed/collapsed.
    const collapsesOnTap = this.isSmallScreen
      ? this.mobileNavOpen()        // drawer open → tapping closes it
      : !this.navCollapsed();       // rail expanded → tapping collapses it
    return collapsesOnTap ? 'Collapse navigation' : 'Expand navigation';
  }

  toggleTheme(): void {
    this.themeService.toggle();
  }

  /** Which status-driven banner (if any) should be showing right now. */
  private computeStatusBannerKey(): string | null {
    const status = this.webapiService.serverStatus();
    const session = this.loginService.userSessionInfo();
    if (status?.status === 'error') {
      return 'error';
    }
    if (status?.need_regenerate_files && session.is_logged_in) {
      return 'warn:regenerate';
    }
    return null;
  }

  /** Keeps the unified banner in sync with the server status (offline / regenerate). */
  private syncStatusBanner(): void {
    const key = this.computeStatusBannerKey();
    // Refresh the retained status notification while an email failure is
    // displayed so dismissal restores the latest status, not stale content.
    if (key === this.lastStatusBannerKey && !this.notification.isEmailDeliveryFailureVisible()) {
      return;
    }
    this.lastStatusBannerKey = key;
    if (key === null) {
      this.notification.clearStatus();
      return;
    }
    if (key === 'error') {
      this.notification.showStatus({
        type: 'error',
        message: this.webapiService.serverStatus()?.message || 'Connection to the server was lost.',
        persistent: true,
      });
    } else if (key === 'warn:regenerate') {
      this.notification.showStatus({
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
