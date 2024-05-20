import { Component, EventEmitter, Output } from '@angular/core';
import { Peer, WebapiService } from '../webapi.service';
import { MessageService } from 'primeng/api';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';

@Component({
  selector: 'app-manage-peers-list',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule],
  providers: [MessageService],
  templateUrl: './manage-peers-list.component.html',
  styleUrl: './manage-peers-list.component.scss'
})
export class ManagePeersListComponent {
  peers: Peer[] = [];

  constructor(private messageService: MessageService, private webapiService: WebapiService) { }

  ngOnInit() {
    this.refreshData();
  }

  refreshData(): void {
    this.webapiService.getPeerList().subscribe(data => {
      this.peers = data;
    });
  }

  @Output() onNewItem = new EventEmitter<Peer>();
  @Output() onEdit = new EventEmitter<Peer>();

  newItem(): void {
    if (this.onNewItem) {
      let peer = {} as Peer;
      this.onNewItem.emit(peer);
      // this.webapiService.getPeer(0).subscribe(peer => {
      //   this.onNewItem.emit(peer);
      // });
    }
  }

  editItem(peer: Peer): void {
    if (this.onEdit) {
      this.onEdit.emit(peer);
    }
  }
}
