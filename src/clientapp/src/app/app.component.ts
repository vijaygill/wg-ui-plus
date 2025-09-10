
import { Component, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import { RouterOutlet } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { SidepanelComponent } from './app-sidepanel/app-sidepanel.component';
import { AppSharedModule } from './app-shared.module';
import { MessageService } from 'primeng/api';
import { PlatformInformation, ServerStatus, UserSessionInfo } from './webapi.entities';
import { Subscription } from 'rxjs';
import { WebapiService } from './webapi.service';
import { LoginService } from './login-service';
import { PlatformInformationService } from './platform-information.service';
import { PeriodicRefreshUiService } from './periodic-refresh-ui.service';

@Component({
    standalone: true,
    selector: 'app-root',
    imports: [RouterModule, RouterOutlet, FormsModule, SidepanelComponent, AppSharedModule],
    providers: [MessageService],
    templateUrl: './app.component.html',
    styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  title = 'WireGuard UI Plus';

  serverStatus: ServerStatus = {
    need_regenerate_files: false,
    application_details: { current_version: '', latest_live_version: '', },
  } as ServerStatus;
  userSessionInfo: UserSessionInfo = { is_logged_in: false, message: '' };

  timerSubscription !: Subscription;
  serverStatusSubscription !: Subscription;
  loginServiceSubscription !: Subscription;
  platformInformationServiceSubscription !: Subscription;

  platformInformation: PlatformInformation = {} as PlatformInformation;

  constructor(private messageService: MessageService,
    private webapiService: WebapiService,
    private loginService: LoginService,
    private platformInformationService: PlatformInformationService,
    private periodicRefreshUiService: PeriodicRefreshUiService) { }

  ngOnInit() {
    // this.primengConfig.zIndex = {
    //   modal: 1100,    // dialog, sidebar
    //   overlay: 1000,  // dropdown, overlaypanel
    //   menu: 1000,     // overlay menus
    //   tooltip: 1100   // tooltip
    // };

    this.platformInformationServiceSubscription = this.platformInformationService.platformInformation.subscribe(
      (data) => {
        this.platformInformation = data;
      }
    );

    this.timerSubscription = this.periodicRefreshUiService.onTimer.subscribe(val => {
      this.webapiService.checkServerStatus();
    });

    this.serverStatusSubscription = this.webapiService.serverStatus.subscribe(data => {
      this.serverStatus = data;
      this.messageService.clear();
      if (this.serverStatus && this.serverStatus.message) {
        let severity = this.serverStatus.status == 'error' ? 'error'
          : this.serverStatus.status == 'ok' ? 'info'
            : 'info';
        this.messageService.add({
          summary: 'Server Status',
          detail: this.serverStatus.message,
          severity: severity,
          closable: false,
        });
      }
    });

    this.loginServiceSubscription = this.loginService.getUserSessionInfo().subscribe(data => {
      this.userSessionInfo = data;
    });
    this.loginService.checkIsUserAuthenticated();
    this.webapiService.checkServerStatus();
    this.platformInformationService.checkPlatform();
  }

  ngOnDestroy() {
    if (this.timerSubscription) {
      this.timerSubscription.unsubscribe();
    }
    if (this.serverStatusSubscription) {
      this.serverStatusSubscription.unsubscribe();
    }
    if (this.loginServiceSubscription) {
      this.loginServiceSubscription.unsubscribe();
    }
    if (this.platformInformationServiceSubscription) {
      this.platformInformationServiceSubscription.unsubscribe();
    }
  }

  applyconfiguration(event: Event): void {
    this.webapiService.generateConfigurationFiles().subscribe(data => {
      this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Configuration files generated on server.' });
      this.webapiService.wireguardRestart().subscribe(() => {
        this.webapiService.checkServerStatus();
        this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Wireguard restarted on server.' });
      });
    });
  }


}
