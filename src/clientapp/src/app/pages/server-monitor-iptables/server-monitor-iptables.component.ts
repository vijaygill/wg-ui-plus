import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { Subscription } from 'rxjs';
import { WebapiService } from '../../services/webapi.service';
import { IptablesLog } from '../../webapi.entities';

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
  ipTablesLog: IptablesLog = { output: '' } as IptablesLog;
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
    this.webapiService.getIptablesLog().subscribe(data => {
      this.ipTablesLog = data;
    }
    );
  }

}
