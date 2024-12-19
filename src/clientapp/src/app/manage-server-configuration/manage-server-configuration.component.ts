import { Component } from '@angular/core';
import { MessageService } from 'primeng/api';
import { ChangeUserPasswordInfo, ServerConfiguration, ServerStatus, ServerValidationError, UserSessionInfo, WireguardConfiguration } from '../webapi.entities';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { ValidationErrorsDisplayComponent } from '../validation-errors-display/validation-errors-display.component';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthorizedViewComponent } from '../authorized-view/authorized-view.component';
import { Subscription } from 'rxjs';
import { Router } from '@angular/router';
import { LoginService } from '../login-service';
import { WebapiService } from '../webapi.service';

@Component({
    standalone: true,
    selector: 'app-manage-server-configuration',
    imports: [CommonModule, FormsModule, AppSharedModule, ValidationErrorsDisplayComponent, AuthorizedViewComponent],
    providers: [MessageService],
    templateUrl: './manage-server-configuration.component.html',
    styleUrl: './manage-server-configuration.component.scss'
})
export class ManageServerConfigurationComponent {

  editItem: ServerConfiguration = {} as ServerConfiguration;
  validationResult!: ServerValidationError;

  changeUserPasswordInfo: ChangeUserPasswordInfo = {} as ChangeUserPasswordInfo;

  serverStatus !: ServerStatus;

  userSessionInfo!: UserSessionInfo;
  loginServiceSubscription !: Subscription;
  serverStatusSubscription !: Subscription;


  constructor(private messageService: MessageService,
    private webapiService: WebapiService,
    private router: Router, private loginService: LoginService) { }

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
          this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Server configuration saved.' });
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
    this.messageService.add({ severity: 'warn', summary: 'Cancel', detail: 'Server configuration reloaded from database.' });
  }

  wireguardConfiguration: WireguardConfiguration = {} as WireguardConfiguration;

  generateWireguardConfig(event: Event): void {
    this.webapiService.generateConfigurationFiles().subscribe(data => {
      this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Configuration files generated on server.' });
    });
  }

  restartWireguard(event: Event): void {
    this.webapiService.wireguardRestart().subscribe(data => {
      this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Wireguard restarted on server.' });
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
