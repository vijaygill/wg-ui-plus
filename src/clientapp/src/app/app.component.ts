import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import { RouterOutlet } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { SidepanelComponent } from './sidepanel/sidepanel.component';
import { AppSharedModule } from './app-shared.module';
import { Message, MessageService, PrimeNGConfig } from 'primeng/api';
import { ServerStatus, UserSessionInfo } from './webapi.entities';
import { Subscription, interval } from 'rxjs';
import { WebapiService } from './webapi.service';
import { LoginService } from './loginService';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterModule, RouterOutlet, FormsModule, SidepanelComponent, AppSharedModule],
  providers: [MessageService],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent implements OnInit {
  title = 'wg-ui-plus';

  serverStatus: ServerStatus = { need_regenerate_files: false, } as ServerStatus;
  userSessionInfo: UserSessionInfo = { is_logged_in: false, message: '' };

  private refresh_timer = interval(5000);
  timerSubscription !: Subscription;
  serverStatusSubscription !: Subscription;
  loginServiceSubscription !: Subscription;

  constructor(private primengConfig: PrimeNGConfig,
    private messageService: MessageService,
    private webapiService: WebapiService,
    private loginService: LoginService) { }

  ngOnInit() {
    // this.primengConfig.zIndex = {
    //   modal: 1100,    // dialog, sidebar
    //   overlay: 1000,  // dropdown, overlaypanel
    //   menu: 1000,     // overlay menus
    //   tooltip: 1100   // tooltip
    // };

    this.timerSubscription = this.refresh_timer.subscribe(val => {
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
  }


  applyconfiguration(event: Event): void {
    this.webapiService.generateConfigurationFiles().subscribe(data => {
      this.messageService.add({ severity: 'success ', summary: 'Success', detail: 'Configuration files generated on server.' });
      this.webapiService.wireguardRestart().subscribe(() => {
        this.webapiService.checkServerStatus();
        this.messageService.add({ severity: 'success ', summary: 'Success', detail: 'Wireguard restarted on server.' });
      });
    });
  }


}
