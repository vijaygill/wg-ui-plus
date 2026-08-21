import { Component, OnInit, ChangeDetectionStrategy, effect, signal } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../../app-shared.module';
import { Router } from '@angular/router';
import { UserCredentials } from '../../webapi.entities';
import { LoginService } from '../../services/login.service';

@Component({
    standalone: true,
    selector: 'app-login',
    imports: [FormsModule, AppSharedModule],
    templateUrl: './login.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './login.component.scss'
})
export class LoginComponent implements OnInit {
  credentials: UserCredentials = { username: '', password: '' } as UserCredentials;

  /** Feedback shown under the form (progress note, then the server's message). */
  message = signal('');

  url !: string;

  constructor(private router: Router, private loginService: LoginService) {
    // React to session updates (e.g. the login response): surface the returned
    // message and advance to the home page once logged in.
    effect(() => {
      const session = this.loginService.userSessionInfo();
      this.message.set(session.message);
      if (session.is_logged_in) {
        this.router.navigate(['/']);
      }
    });
  }

  ngOnInit(): void {
    this.url = this.router.url;
  }

  onSubmit()
  {
    this.message.set('Logging in. Please wait...');
    this.loginService.login(this.credentials);
  }
}
