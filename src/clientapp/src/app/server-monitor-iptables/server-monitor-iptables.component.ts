import { Component, OnInit } from '@angular/core';
import { Subscription, interval } from 'rxjs';
import { WebapiService } from '../webapi.service';
import { IpTablesLog } from '../webapi.entities';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { MessageService } from 'primeng/api';
import { PeriodicRefreshUiService } from '../periodic-refresh-ui.service';

@Component({
    standalone: true,
    selector: 'app-server-monitor-iptables',
    imports: [CommonModule, FormsModule, AppSharedModule],
    providers: [MessageService],
    templateUrl: './server-monitor-iptables.component.html',
    styleUrl: './server-monitor-iptables.component.scss'
})
export class ServerMonitorIptablesComponent implements OnInit {
  private timerSubscription !: Subscription;
  ipTablesLog: IpTablesLog = { output: '' } as IpTablesLog;
  refreshDelay: number = 0;


  constructor(private webapiService: WebapiService,
    private periodicRefreshUiService: PeriodicRefreshUiService) {
  }

  ngOnInit(): void {
    this.subscribeTimer();
  }

  ngOnDestroy() {
    this.unsubscribeTimer();
  }

  subscribeTimer(): void {
    this.timerSubscription = this.periodicRefreshUiService.onTimer.subscribe(val => {
      this.refreshDelay = val;
      this.loadData();
    });
    this.periodicRefreshUiService.performRefresh();
  }

  unsubscribeTimer(): void {
    if (this.timerSubscription) {
      this.timerSubscription.unsubscribe();
    }
  }

  loadData() {
    this.webapiService.getIpTablesLog().subscribe(data => {
      this.ipTablesLog = data;
    }
    );
  }

}
