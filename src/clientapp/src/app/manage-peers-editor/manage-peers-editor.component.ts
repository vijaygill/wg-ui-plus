import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { Peer, PeerGroup, ServerValidationError, WebapiService } from '../webapi.service';
import { MessageService } from 'primeng/api';
import { AppSharedModule } from '../app-shared.module';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { nextTick } from 'process';
import { HttpErrorResponse } from '@angular/common/http';
import { ValidationErrorsDisplayComponent } from '../validation-errors-display/validation-errors-display.component';

@Component({
  selector: 'app-manage-peers-editor',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule, ValidationErrorsDisplayComponent],
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
      if (this.peer) {
        this.webapiService.getPeerGroupList().subscribe(lookup => {
          let lookupItems = this.peer.peer_groups ?
            lookup.filter(x => !this.peer.peer_groups.some(y => y.id === x.id))
            : lookup;
          this.peer.peer_groups_lookup = lookupItems;
        });
      }
    });
  }

  peer: Peer = {} as Peer;

  validationResult!: ServerValidationError;

  @Output() onFinish = new EventEmitter<boolean>();

  constructor(private messageService: MessageService, private webapiService: WebapiService) { }

  ok() {
    if (!this.peer) {
      return;
    }
    this.peer.peer_group_ids = this.peer.peer_groups ? this.peer.peer_groups.map(x => x.id) : [];
    this.webapiService.savePeer(this.peer)
      .subscribe({
        next: data => {
        },
        error: error => {
          let response = error as HttpErrorResponse;
          if (response) {
            this.validationResult = response.error as ServerValidationError;
          }
        },
        complete: () => {
          this.onFinish.emit(true);
        },
      });
  }

  cancel() {
    this.onFinish.emit(false);
  }

  peerGroupsPickListTrackBy(index: number, item: any) {
    let x = item as PeerGroup;
    return x.id;
  }
}
