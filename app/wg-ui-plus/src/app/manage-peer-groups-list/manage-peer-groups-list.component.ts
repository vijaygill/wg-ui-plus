import { Component, EventEmitter, Input, Output } from '@angular/core';
import { PeerGroup, WebapiService } from '../webapi.service';
import { MessageService } from 'primeng/api';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PrimeNGModule } from '../primeng.module';

@Component({
  selector: 'app-manage-peer-groups-list',
  standalone: true,
  imports: [CommonModule, FormsModule, PrimeNGModule],
  providers: [MessageService],
  templateUrl: './manage-peer-groups-list.component.html',
  styleUrl: './manage-peer-groups-list.component.scss'
})
export class ManagePeerGroupsListComponent {
  peerGroups: PeerGroup[] = [];

  constructor(private messageService: MessageService, private webapiService: WebapiService) { }

  ngOnInit() {
    this.refreshData();
  }

  refreshData(): void {
    this.webapiService.getPeerGroupList().subscribe(data => {
      this.peerGroups = data;
    });
  }

  @Output() onEdit = new EventEmitter<PeerGroup>();

  editItem(peerGroup: PeerGroup): void {
    if (this.onEdit) {
      this.onEdit.emit(peerGroup);
    }
  }
}