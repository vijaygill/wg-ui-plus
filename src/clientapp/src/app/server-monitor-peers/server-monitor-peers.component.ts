import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { MessageService } from 'primeng/api';
import { ConnectedPeerInformation } from '../webapi.entities';
import { Subscription, interval } from 'rxjs';
import { WebapiService } from '../webapi.service';

@Component({
  selector: 'app-server-monitor-peers',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule],
  providers: [MessageService],
  templateUrl: './server-monitor-peers.component.html',
  styleUrl: './server-monitor-peers.component.scss'
})
export class ServerMonitorPeersComponent implements OnInit {
  connectedPeerData: ConnectedPeerInformation = { datetime: '', items: [], } as ConnectedPeerInformation;

  private refresh_timer = interval(10000);
  timerSubscription !: Subscription;

  constructor(private webapiService: WebapiService) {
  }

  ngOnInit(): void {
    this.subscribeTimer();
  }

  ngOnDestroy() {
    this.unsubscribeTimer();
  }

  subscribeTimer(): void {
    this.timerSubscription = this.refresh_timer.subscribe(val => {
      this.loadData();
    });
    this.loadData();
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
