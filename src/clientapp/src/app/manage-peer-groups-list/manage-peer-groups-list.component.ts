import { Component, EventEmitter, Input, Output } from '@angular/core';
import { PeerGroup, WebapiService } from '../webapi.service';
import { MessageService } from 'primeng/api';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';

@Component({
  selector: 'app-manage-peer-groups-list',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule],
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

  @Output() onNewItem = new EventEmitter<PeerGroup>();
  @Output() onEdit = new EventEmitter<PeerGroup>();

  newItem(): void {
    if (this.onNewItem) {
      let peerGroup = {} as PeerGroup;
      this.onNewItem.emit(peerGroup);
    }
  }

  editItem(peerGroup: PeerGroup): void {
    if (this.onEdit) {
      this.onEdit.emit(peerGroup);
    }
  }
}
