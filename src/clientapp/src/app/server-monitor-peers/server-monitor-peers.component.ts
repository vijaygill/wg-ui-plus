import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { MessageService } from 'primeng/api';
import { ConnectedPeerInformation } from '../webapi.entities';
import { Subscription } from 'rxjs';
import { WebapiService } from '../webapi.service';
import { PeriodicRefreshUiService } from '../periodic-refresh-ui.service';

@Component({
  selector: 'app-server-monitor-peers',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule],
  providers: [MessageService],
  templateUrl: './server-monitor-peers.component.html',
  styleUrl: './server-monitor-peers.component.scss'
})
export class ServerMonitorPeersComponent implements OnInit {
  connectedPeerData: ConnectedPeerInformation = { datetime: '', items: [], message: '' } as ConnectedPeerInformation;
  timerSubscription !: Subscription;
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
    this.webapiService.getConnectedPeers().subscribe(data => {
      this.connectedPeerData = data;
    });
  }

}
