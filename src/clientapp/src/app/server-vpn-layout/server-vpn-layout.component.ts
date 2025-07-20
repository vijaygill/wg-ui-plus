import { Component, OnInit } from '@angular/core';
import { MessageService, TreeNode } from 'primeng/api';
import { Subscription, interval } from 'rxjs';
import { WebapiService } from '../webapi.service';

import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { PeriodicRefreshUiService } from '../periodic-refresh-ui.service';

@Component({
    standalone: true,
    selector: 'app-server-vpn-layout',
    imports: [FormsModule, AppSharedModule],
    providers: [MessageService],
    templateUrl: './server-vpn-layout.component.html',
    styleUrl: './server-vpn-layout.component.scss'
})
export class ServerVpnLayoutComponent implements OnInit {
  private timerSubscription !: Subscription;
  heirarchyData!: TreeNode[];
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
    this.webapiService.getTargetHeirarchy().subscribe(data => {
      this.heirarchyData = data;
    }
    );
  }

}
