import { ChangeDetectorRef, Component, Injectable, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { HttpErrorResponse } from '@angular/common/http';
import { ValidationErrorsDisplayComponent } from '../validation-errors-display/validation-errors-display.component';
import { WebapiService } from '../webapi.service';
import { Router } from '@angular/router';
import { Observable, Subject, Subscription } from 'rxjs';
import { UserCrendentials, UserSessionInfo } from '../webapi.entities';
import { LoginService } from '../login-service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule, ValidationErrorsDisplayComponent],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent implements OnInit {
  credentials: UserCrendentials = { username: '', password: '' } as UserCrendentials;
  userSessionInfo: UserSessionInfo = { is_logged_in: false, message: '' } as UserSessionInfo;
  loginServiceSubscription !: Subscription;
  url !: string;

  constructor(private router: Router, private loginService: LoginService) {

  }

  ngOnInit(): void {
    this.url = this.router.url;
    this.loginServiceSubscription = this.loginService.getUserSessionInfo().subscribe(data => {
      this.userSessionInfo = data;
      if (this.userSessionInfo.is_logged_in) {
        this.router.navigate(['/']);
      }
    });
  }

  ngOnDestroy() {
    if (this.loginServiceSubscription) {
      this.loginServiceSubscription.unsubscribe();
    }
  }

  login(event: Event): void {
    this.userSessionInfo.message = 'Logging in. Please wait...';
    this.loginService.login(this.credentials);
  }

  logout(event: Event): void {
    this.loginService.logout();
  }
}

