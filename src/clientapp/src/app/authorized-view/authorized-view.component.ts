import { CommonModule } from '@angular/common';
import { Component, ContentChild, OnInit, TemplateRef } from '@angular/core';
import { AppSharedModule } from '../app-shared.module';
import { LoginService } from '../login/login.component';
import { Router } from '@angular/router';
import { UserSessionInfo } from '../webapi.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-authorized-view',
  standalone: true,
  imports: [CommonModule, AppSharedModule],
  templateUrl: './authorized-view.component.html',
  styleUrl: './authorized-view.component.scss'
})
export class AuthorizedViewComponent implements OnInit{
  userSessionInfo!: UserSessionInfo;
  loginServiceSubscription !: Subscription;

  @ContentChild("childControl") childControl!: TemplateRef<any>;

  constructor(private router: Router, private loginService: LoginService) { }

  ngOnInit(): void {
    this.loginServiceSubscription = this.loginService.getUserSessionInfo().subscribe(data => {
      this.userSessionInfo = data;
      if (this.userSessionInfo.is_logged_in) {
        this.router.navigate(['/home']);
      }
      else {
        this.router.navigate(['/']);
      }
    });
    this.loginService.checkIsUserAuthenticated();
  }

  ngOnDestroy() {
    if (this.loginServiceSubscription) {
      this.loginServiceSubscription.unsubscribe();
    }
  }
}
