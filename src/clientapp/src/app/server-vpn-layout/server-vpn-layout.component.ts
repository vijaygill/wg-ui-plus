import { Component, OnInit } from '@angular/core';
import { MessageService, TreeNode } from 'primeng/api';
import { Subscription, interval } from 'rxjs';
import { WebapiService } from '../webapi.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';

@Component({
  selector: 'app-server-vpn-layout',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule],
  providers: [MessageService],
  templateUrl: './server-vpn-layout.component.html',
  styleUrl: './server-vpn-layout.component.scss'
})
export class ServerVpnLayoutComponent implements OnInit {
  private refresh_timer = interval(5000);
  private timerSubscription !: Subscription;
  heirarchyData!: TreeNode[];

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
    this.webapiService.getTargetHeirarchy().subscribe(data => {
      this.heirarchyData = data;
    }
    );
  }

}
