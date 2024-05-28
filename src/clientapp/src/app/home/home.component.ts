import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Observable, Subscription, interval, timer } from 'rxjs';

import { AppSharedModule } from '../app-shared.module';
import { MessageService, TreeNode } from 'primeng/api';
import { ConnectedPeerInformation, WebapiService } from '../webapi.service';
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

  heirarchyData!: TreeNode[];
  connectedPeerData: ConnectedPeerInformation = { datetime: '', items: [], } as ConnectedPeerInformation;

  private refresh_timer = interval(5000);
  subscriptionDataConnectedPeers !: Subscription;

  constructor(private webapiService: WebapiService) {
  }

  ngOnInit(): void {
    this.subscribeTimer();
  }

  ngOnDestroy() {
    this.unsubscribeTimer();
  }

  subscribeTimer(): void {
    this.subscriptionDataConnectedPeers = this.refresh_timer.subscribe(val => {
      this.loadDataConnectedPeers();
    });
    this.loadDataConnectedPeers();
  }

  unsubscribeTimer(): void {
    if (this.subscriptionDataConnectedPeers) {
      this.subscriptionDataConnectedPeers.unsubscribe();
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


  onTabChange(event: any) {
    if (event.index == 0) {
      this.subscribeTimer()
    }
    if (event.index == 1) {
      this.unsubscribeTimer()
      this.loadDataTargetHeirarchy();
    }
  }


}
