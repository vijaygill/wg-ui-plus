import { Component, OnInit, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';
import { Subscription } from 'rxjs';
import { WebapiService } from '../../services/webapi.service';
import { OrgChartNode } from '../../webapi.entities';

import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../../app-shared.module';
import { PeriodicRefreshUiService } from '../../services/periodic-refresh-ui.service';

@Component({
    standalone: true,
    selector: 'app-server-vpn-layout',
    imports: [FormsModule, AppSharedModule],
    templateUrl: './server-vpn-layout.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './server-vpn-layout.component.scss'
})
export class ServerVpnLayoutComponent implements OnInit {
  private timerSubscription !: Subscription;
  hierarchyData!: OrgChartNode[];
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
    this.webapiService.getTargetHierarchy().subscribe(data => {
      this.hierarchyData = data;
      this.cdr.markForCheck();
    }
    );
  }

}
