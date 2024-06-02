import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { HttpErrorResponse } from '@angular/common/http';
import { ValidationErrorsDisplayComponent } from '../validation-errors-display/validation-errors-display.component';
import { UserCrendentials, UserSessionInfo, WebapiService } from '../webapi.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule, ValidationErrorsDisplayComponent],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent implements OnInit {
  credentials: UserCrendentials = { username: '', password: '' } as UserCrendentials;
  userSessionInfo!: UserSessionInfo;

  constructor(private webapiService: WebapiService) {

  }

  ngOnInit(): void {
    this.webapiService.checkIsUserAuthenticated().subscribe(data => {
      this.userSessionInfo = data;
    });
  }

  login(event: Event): void {
    this.webapiService.login(this.credentials).subscribe(data => {
      this.userSessionInfo = data;
    });
  }

  logout(event: Event): void {
    this.webapiService.logout().subscribe(data => {
      this.userSessionInfo = data;
    });
  }
}
