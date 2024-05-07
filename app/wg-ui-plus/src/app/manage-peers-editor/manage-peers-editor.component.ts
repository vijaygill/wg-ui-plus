import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { Peer, PeerGroup, WebapiService } from '../webapi.service';
import { MessageService } from 'primeng/api';
import { CrudContainerComponent } from '../crud-container/crud-container.component';
import { ManagePeersListComponent } from '../manage-peers-list/manage-peers-list.component';
import { PrimeNGModule } from '../primeng.module';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-manage-peers-editor',
  standalone: true,
  imports: [CommonModule, FormsModule, PrimeNGModule],
  templateUrl: './manage-peers-editor.component.html',
  styleUrl: './manage-peers-editor.component.scss'
})
export class ManagePeersEditorComponent {
  @Input()
  get editItem(): Peer { return this.peer; }
  set editItem(value: Peer) {
    this.peer = value;
    this.webapiService.getPeer(value.id).subscribe(data => {
      this.peer = data;
    });
  }

  peer: Peer = {} as Peer;

  peer_group: PeerGroup | undefined;

  @Output() onFinish = new EventEmitter<boolean>();

  constructor(private messageService: MessageService, private webapiService: WebapiService) { }

  ok() {
    this.webapiService.savePeer(this.peer).subscribe(data => {
      this.onFinish.emit(true);
    });
  }

  cancel() {
    this.onFinish.emit(false);
  }

}
