import { CommonModule } from '@angular/common';
import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../../app-shared.module';
import { Sort } from '@angular/material/sort';
import { ConnectedPeerInformation } from '../../webapi.entities';
import { Subscription } from 'rxjs';
import { WebapiService } from '../../services/webapi.service';
import { PeriodicRefreshUiService } from '../../services/periodic-refresh-ui.service';

@Component({
    standalone: true,
    selector: 'app-server-monitor-peers',
    imports: [CommonModule, FormsModule, AppSharedModule],
    templateUrl: './server-monitor-peers.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './server-monitor-peers.component.scss'
})
export class ServerMonitorPeersComponent implements OnInit {
  connectedPeerData: ConnectedPeerInformation = { datetime: '', items: [], message: '' } as ConnectedPeerInformation;
  timerSubscription !: Subscription;
  loadDataSubscription !: Subscription;
  refreshDelay: number = 0;
  private currentSort: Sort = { active: 'peer_name', direction: 'asc' };

  get connectedCount(): number {
    return this.connectedPeerData.items.filter(i => i.status === 'connected').length;
  }

  get offlineCount(): number {
    return this.connectedPeerData.items.length - this.connectedCount;
  }

  get totalTx(): number {
    return this.connectedPeerData.items.reduce((sum, i) => sum + (i.transfer_tx || 0), 0);
  }

  get totalRx(): number {
    return this.connectedPeerData.items.reduce((sum, i) => sum + (i.transfer_rx || 0), 0);
  }

  constructor(private webapiService: WebapiService,
    private periodicRefreshUiService: PeriodicRefreshUiService) {
  }

  ngOnInit(): void {
    this.subscribeTimer();
  }

  ngOnDestroy() {
    this.unsubscribeTimer();
    if (this.loadDataSubscription) {
      this.loadDataSubscription.unsubscribe();
    }
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
    this.loadDataSubscription = this.webapiService.getConnectedPeers().subscribe(data => {
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
