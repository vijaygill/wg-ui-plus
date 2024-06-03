import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Observable, Subscription, interval, timer } from 'rxjs';

import { AppSharedModule } from '../app-shared.module';
import { MessageService, TreeNode } from 'primeng/api';
import { ConnectedPeerInformation, IpTablesLog } from '../webapi.entities';
import { WebapiService } from '../webapi.service';
import { TabViewChangeEvent } from 'primeng/tabview';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule],
  providers: [MessageService],
  templateUrl: `./home.component.html`,
  styleUrl: './home.component.scss'
})
export class HomeComponent implements OnInit {
  activeTab: number = 0;
  heirarchyData!: TreeNode[];
  connectedPeerData: ConnectedPeerInformation = { datetime: '', items: [], } as ConnectedPeerInformation;
  ipTablesLog: IpTablesLog = { output: '' } as IpTablesLog;

  private refresh_timer = interval(5000);
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

  onTabChange(event: any) {
    this.activeTab = event.index;
    this.loadData();
  }

  loadData() {
    if (this.activeTab == 0) {
      this.loadDataConnectedPeers();
    }
    if (this.activeTab == 1) {
      this.loadDataTargetHeirarchy();
    }
    if (this.activeTab == 2) {
      this.loadDataIpTablesLog();
    }
  }

  loadDataTargetHeirarchy() {
    this.webapiService.getTargetHeirarchy().subscribe(data => {
      this.heirarchyData = data;
    }
    );
  }

  loadDataConnectedPeers() {
    this.webapiService.getConnectedPeers().subscribe(data => {
      this.connectedPeerData = data;
    }
    );
  }

  loadDataIpTablesLog() {
    this.webapiService.getIpTablesLog().subscribe(data => {
      this.ipTablesLog = data;
    }
    );
  }


}
