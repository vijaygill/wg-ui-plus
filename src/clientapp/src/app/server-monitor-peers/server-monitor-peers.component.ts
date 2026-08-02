import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { Sort } from '@angular/material/sort';
import { ConnectedPeerInformation } from '../webapi.entities';
import { Subscription } from 'rxjs';
import { WebapiService } from '../webapi.service';
import { PeriodicRefreshUiService } from '../periodic-refresh-ui.service';

@Component({
    standalone: true,
    selector: 'app-server-monitor-peers',
    imports: [CommonModule, FormsModule, AppSharedModule],
    templateUrl: './server-monitor-peers.component.html',
    styleUrl: './server-monitor-peers.component.scss'
})
export class ServerMonitorPeersComponent implements OnInit {
  connectedPeerData: ConnectedPeerInformation = { datetime: '', items: [], message: '' } as ConnectedPeerInformation;
  timerSubscription !: Subscription;
  refreshDelay: number = 0;
  private currentSort: Sort = { active: 'peer_name', direction: 'asc' };

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
    this.webapiService.getConnectedPeers().subscribe(data => {
      this.connectedPeerData = data;
      // Re-apply the current sort so the user's chosen ordering survives the
      // periodic refresh (default: sorted by peer name, as before).
      this.sortData(this.currentSort);
    });
  }

  sortData(sort: Sort): void {
    this.currentSort = sort;
    const items = this.connectedPeerData.items;
    if (!sort.active || sort.direction === '') {
      return;
    }
    // Assign a new array so the @for view re-diffs on interactive sorting.
    const sorted = [...items].sort((a, b) => {
      const aValue = String((a as any)[sort.active] ?? '');
      const bValue = String((b as any)[sort.active] ?? '');
      const cmp = aValue.localeCompare(bValue);
      return sort.direction === 'asc' ? cmp : -cmp;
    });
    this.connectedPeerData.items = sorted;
  }

}
