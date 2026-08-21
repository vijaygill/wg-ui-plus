import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { Subscription } from 'rxjs';
import { WebapiService } from '../../services/webapi.service';
import { IpTablesLog } from '../../webapi.entities';

import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../../app-shared.module';
import { PeriodicRefreshUiService } from '../../services/periodic-refresh-ui.service';

@Component({
    standalone: true,
    selector: 'app-server-monitor-iptables',
    imports: [FormsModule, AppSharedModule],
    templateUrl: './server-monitor-iptables.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './server-monitor-iptables.component.scss'
})
export class ServerMonitorIptablesComponent implements OnInit {
  private timerSubscription !: Subscription;
  ipTablesLog: IpTablesLog = { output: '' } as IpTablesLog;
  refreshDelay: number = 0;


  constructor(private webapiService: WebapiService,
    private periodicRefreshUiService: PeriodicRefreshUiService,
    private cdr: ChangeDetectorRef) {
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
      this.cdr.markForCheck();
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
      this.cdr.markForCheck();
    }
    );
  }

}
