import { Injectable, signal } from '@angular/core';
import { WebapiService } from './webapi.service';
import { UserCredentials, UserSessionInfo } from '../webapi.entities';

@Injectable({ providedIn: 'root' })
export class LoginService {

  /** Session exposed before the first authentication response arrives. */
  private userSessionSignal = signal<UserSessionInfo>({ is_logged_in: false, message: '' });

  /**
   * Current session info. Late readers get the current value immediately
   * (previously only new emissions were delivered to late subscribers).
   */
  readonly userSessionInfo = this.userSessionSignal.asReadonly();

  constructor(private webapiService: WebapiService) { }

  checkIsUserAuthenticated(): void {
    this.webapiService.checkIsUserAuthenticated().subscribe(data => {
      this.userSessionSignal.set(data);
    });
  }

  login(credentials: UserCredentials): void {
    this.webapiService.login(credentials).subscribe(data => {
      this.userSessionSignal.set(data);
    });
  }

  logout(): void {
    this.webapiService.logout().subscribe(data => {
      this.userSessionSignal.set(data);
    });
  }

}
