import { CommonModule } from '@angular/common';
import { Component, ContentChild, TemplateRef, ChangeDetectionStrategy, effect } from '@angular/core';
import { AppSharedModule } from '../../app-shared.module';
import { LoginService } from '../../services/login.service';
import { Router } from '@angular/router';
import { UserSessionInfo } from '../../webapi.entities';

@Component({
    standalone: true,
    selector: 'app-authorized-view',
    imports: [CommonModule, AppSharedModule],
    templateUrl: './authorized-view.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './authorized-view.component.scss'
})
export class AuthorizedViewComponent {

  /** Reactive view of the current session info. */
  readonly userSessionInfo = this.loginService.userSessionInfo;

  /** Last session value seen by the redirect effect (null until its first run). */
  private lastSeenSession: UserSessionInfo | null = null;

  /**
   * Redirects to the login page whenever the session turns logged-out.
   * The seeded placeholder is skipped so an authenticated user opening a
   * protected page is not redirected before the authentication check lands.
   */
  private readonly sessionRedirect = effect(() => {
    const session = this.loginService.userSessionInfo();
    const seen = this.lastSeenSession;
    this.lastSeenSession = session;
    if (seen !== null && !session.is_logged_in) {
      this.router.navigate(['/login']);
    }
  });

  @ContentChild("childControl") childControl!: TemplateRef<any>;

  constructor(private router: Router, private loginService: LoginService) {
    this.loginService.checkIsUserAuthenticated();
  }
}
