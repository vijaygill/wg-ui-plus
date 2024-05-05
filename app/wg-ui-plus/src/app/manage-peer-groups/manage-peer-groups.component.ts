import { Component } from '@angular/core';
import { MessageService } from 'primeng/api';
import { PeerGroup, WebapiService } from '../webapi.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PrimeNGModule } from '../primeng.module';

@Component({
  selector: 'app-manage-peer-groups',
  standalone: true,
  imports: [CommonModule, FormsModule, PrimeNGModule],
  providers: [MessageService],
  templateUrl: './manage-peer-groups.component.html',
  styleUrl: './manage-peer-groups.component.scss'
})
export class ManagePeerGroupsComponent {

  peerGroups: PeerGroup[] = [];

  constructor(private messageService: MessageService, private webapiService: WebapiService) { }

  ngOnInit() {
    this.refreshData();
  }

  refreshData() {
    this.webapiService.getPeerGroupList().subscribe(data => {
      this.peerGroups = data;
    });
  }
}
