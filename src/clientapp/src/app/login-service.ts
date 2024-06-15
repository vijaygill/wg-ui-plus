import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';
import { WebapiService } from './webapi.service';
import { UserCrendentials, UserSessionInfo } from './webapi.entities';

@Injectable({ providedIn: 'root' })
export class LoginService {

  constructor(private webapiService: WebapiService) { }

  private userSessionInfo = new Subject<UserSessionInfo>();

  getUserSessionInfo(): Observable<UserSessionInfo> {
    return this.userSessionInfo.asObservable();
  }

  checkIsUserAuthenticated(): void {
    this.webapiService.checkIsUserAuthenticated().subscribe(data => {
      this.userSessionInfo.next(data);
    });
  }

  login(credentials: UserCrendentials): void {
    this.webapiService.login(credentials).subscribe(data => {
      this.userSessionInfo.next(data);
    });
  }

  logout(): void {
    this.webapiService.logout().subscribe(data => {
      this.userSessionInfo.next(data);
    });
  }

}