import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { Peer, PeerGroup, ServerValidationError, } from '../webapi.entities';
import { WebapiService } from '../webapi.service';
import { MessageService } from 'primeng/api';
import { AppSharedModule } from '../app-shared.module';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { ValidationErrorsDisplayComponent } from '../validation-errors-display/validation-errors-display.component';
import { DomSanitizer } from '@angular/platform-browser';
import { ConfirmationDialogService } from '../confirmation-dialog-service';

@Component({
  selector: 'app-manage-peers-editor',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule, ValidationErrorsDisplayComponent],
  providers: [MessageService, ConfirmationDialogService],
  templateUrl: './manage-peers-editor.component.html',
  styleUrl: './manage-peers-editor.component.scss'
})
export class ManagePeersEditorComponent {
  @Input()
  get editItem(): Peer { return this.peer; }
  set editItem(value: Peer) {
    this.peer = value;
    if (value.id) {
      this.webapiService.getPeer(value.id).subscribe(data => {
        this.peer = data;
        this.getLookupData();
      });
    }
    else {
      this.getLookupData();
    }
  }

  peer: Peer = {} as Peer;

  validationResult!: ServerValidationError;

  @Output() onFinish = new EventEmitter<boolean>();

  constructor(private messageService: MessageService,
    private webapiService: WebapiService,
    private confirmationDialogService: ConfirmationDialogService,
    private sanitizer: DomSanitizer) {

  }

  getLookupData() {
    if (this.peer) {
      this.webapiService.getPeerGroupList().subscribe(lookup => {
        let lookupItems = this.peer.peer_groups ?
          lookup.filter(x => !this.peer.peer_groups.some(y => y.id === x.id) && !x.is_everyone_group)
          : lookup;
        this.peer.peer_groups_lookup = lookupItems;
      });
    }
  }

  getQrCode() {
    let imagePath = this.editItem.qr ? 'data:image/jpg;base64,' + this.editItem.qr : '';
    return imagePath;
  }

  ok() {
    if (!this.peer) {
      return;
    }
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

  delete(event: Event) {
    if (!this.peer) {
      return;
    }

    this.confirmationDialogService.confirm('Confirm', 'Are you sure that you want to delete ' + this.editItem.name + '?')
      .subscribe(dialogResult => {
        if (dialogResult) {
          this.webapiService.deletePeer(this.peer)
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
      });

  }

  peerGroupsPickListTrackBy(index: number, item: any) {
    let x = item as PeerGroup;
    return x.id;
  }

  fileUrl: any;

  downloadConfigFile(event: Event): void {
    if (this.peer.configuration) {
      var blob = new Blob([this.peer.configuration], { type: 'text/plain' });
      // TODO revisit this
      //this.fileUrl = this.sanitizer.bypassSecurityTrustResourceUrl(window.URL.createObjectURL(blob));
      this.fileUrl = window.URL.createObjectURL(blob);
    }
    const downloadAncher = document.createElement("a");
    downloadAncher.style.display = "none";
    downloadAncher.href = this.fileUrl;
    downloadAncher.download = this.peer.name.replace(/[^a-z0-9]+/gi, '') + '.conf';
    downloadAncher.click();
  }

}
