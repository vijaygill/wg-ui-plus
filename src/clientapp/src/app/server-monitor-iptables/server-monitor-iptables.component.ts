import { Component, OnInit } from '@angular/core';
import { Subscription, interval } from 'rxjs';
import { WebapiService } from '../webapi.service';
import { IpTablesLog } from '../webapi.entities';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-server-monitor-iptables',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule],
  providers: [MessageService],
  templateUrl: './server-monitor-iptables.component.html',
  styleUrl: './server-monitor-iptables.component.scss'
})
export class ServerMonitorIptablesComponent implements OnInit {
  private refresh_timer = interval(10000);
  private timerSubscription !: Subscription;
  ipTablesLog: IpTablesLog = { output: '' } as IpTablesLog;


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
    this.webapiService.getIpTablesLog().subscribe(data => {
      this.ipTablesLog = data;
    }
    );
  }

}
