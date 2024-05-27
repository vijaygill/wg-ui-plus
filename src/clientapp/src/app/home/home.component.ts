import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { interval, timer } from 'rxjs';

import { AppSharedModule } from '../app-shared.module';
import { MessageService, TreeNode } from 'primeng/api';
import { ConnectedPeerInformation, WebapiService } from '../webapi.service';

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
  connectedPeerData!: ConnectedPeerInformation;
  private refresh_timer = interval(5000);

  constructor(private webapiService: WebapiService) {
  }

  ngOnInit(): void {
    const sub = this.refresh_timer.subscribe(val => {
      this.loadData();
    });
    this.loadData();
  }

  loadData() {
    this.webapiService.getTargetHeirarchy().subscribe(data => {
      this.heirarchyData = data;
    }
    );

    this.webapiService.getConnectedPeers().subscribe(data => {
      this.connectedPeerData = data;
    }
    );


  }


}
