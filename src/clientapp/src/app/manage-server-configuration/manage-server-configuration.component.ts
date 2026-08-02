import { Component, OnDestroy } from '@angular/core';
import { ChangeUserPasswordInfo, ServerConfiguration, ServerStatus, ServerValidationError, UserSessionInfo, WireguardConfiguration } from '../webapi.entities';

import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { ValidationErrorsDisplayComponent } from '../validation-errors-display/validation-errors-display.component';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthorizedViewComponent } from '../authorized-view/authorized-view.component';
import { Subscription } from 'rxjs';
import { Router } from '@angular/router';
import { LoginService } from '../login-service';
import { WebapiService } from '../webapi.service';
import { NotificationService } from '../notification.service';
import { EditStateService } from '../edit-state.service';

@Component({
  standalone: true,
  selector: 'app-manage-server-configuration',
  imports: [FormsModule, AppSharedModule, ValidationErrorsDisplayComponent, AuthorizedViewComponent],
  templateUrl: './manage-server-configuration.component.html',
  styleUrl: './manage-server-configuration.component.scss'
})
export class ManageServerConfigurationComponent implements OnDestroy {

  editItem: ServerConfiguration = {} as ServerConfiguration;
  validationResult!: ServerValidationError;

  changeUserPasswordInfo: ChangeUserPasswordInfo = {} as ChangeUserPasswordInfo;

  serverStatus !: ServerStatus;

  userSessionInfo!: UserSessionInfo;
  loginServiceSubscription !: Subscription;
  serverStatusSubscription !: Subscription;


  constructor(private notification: NotificationService,
    private webapiService: WebapiService,
    private router: Router, private loginService: LoginService, private editStateService: EditStateService) {
    this.editStateService.setEditing(true);
  }

  ngOnInit(): void {
    this.loginServiceSubscription = this.loginService.getUserSessionInfo().subscribe(data => {
      this.userSessionInfo = data;
      this.userSessionInfo.message = "";
      if (!this.userSessionInfo.is_logged_in) {
        this.router.navigate(['/login']);
      }
    });
    this.loginService.checkIsUserAuthenticated();
    this.serverStatusSubscription = this.webapiService.serverStatus.subscribe(data => {
      if (!this.serverStatus || (this.serverStatus && data && this.serverStatus.last_db_change_datetime < data.last_db_change_datetime)) {
        this.refreshData();
        this.serverStatus = data;
      }
    });
    this.refreshData();
  }

  ngOnDestroy() {
    if (this.loginServiceSubscription) {
      this.loginServiceSubscription.unsubscribe();
    }
    if (this.serverStatusSubscription) {
      this.serverStatusSubscription.unsubscribe();
    }
    this.editStateService.setEditing(false);
  }

  refreshData(): void {
    // get the server configurations and use only first
    this.webapiService.getServerConfigurationList().subscribe(data => {
      this.editItem = data[0];
    });
  }

  ok() {
    this.webapiService.saveServerConfiguration(this.editItem)
      .subscribe({
        next: data => {
          this.notification.success('Server configuration saved.');
          this.validationResult = { type: '', errors: [] } as ServerValidationError;
        },
        error: error => {
          let response = error as HttpErrorResponse;
          if (response) {
            this.validationResult = response.error as ServerValidationError;
          }
        },
        complete: () => {
          this.refreshData()
        },
      });
  }


  cancel() {
    this.refreshData();
    this.notification.warn('Server configuration reloaded from database.');
  }

  wireguardConfiguration: WireguardConfiguration = {} as WireguardConfiguration;

  applyConfiguration(): void {
    this.webapiService.generateConfigurationFiles().subscribe(data => {
      this.notification.success('Configuration files generated on server.');
      this.webapiService.wireguardRestart().subscribe(() => {
        this.webapiService.checkServerStatus();
        this.notification.success('Wireguard restarted on server.');
      });
    });
  }

  changePassword(event: Event): void {
    if (this.changeUserPasswordInfo.new_password !== this.changeUserPasswordInfo.new_password_copy) {
      this.userSessionInfo.message = "New Passwords don't match.";
    }
    else {
      this.webapiService.changeUserPassword(this.changeUserPasswordInfo).subscribe(data => {
        this.userSessionInfo.message = data.message;
      });
    }
  }

}
