import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { Peer, PeerGroup, ServerValidationError, } from '../webapi.entities';
import { WebapiService } from '../webapi.service';
import { AppSharedModule } from '../app-shared.module';

import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { ValidationErrorsDisplayComponent } from '../validation-errors-display/validation-errors-display.component';
import { DomSanitizer } from '@angular/platform-browser';
import { ConfirmationDialogService } from '../confirmation-dialog.service';
import { NotificationService } from '../notification.service';

@Component({
  standalone: true,
  selector: 'app-manage-peers-editor',
  imports: [FormsModule, AppSharedModule, ValidationErrorsDisplayComponent],
  templateUrl: './manage-peers-editor.component.html',
  styleUrl: './manage-peers-editor.component.scss'
})
export class ManagePeersEditorComponent {
  @Input()
  get editItem(): Peer { return this.peer; }
  set editItem(value: Peer) {
    this.peer = value;
    this.captureSnapshot();
    if (value.id) {
      this.webapiService.getPeer(value.id).subscribe(data => {
        this.peer = data;
        this.getLookupData();
        this.captureSnapshot();
      });
    }
    else {
      this.getLookupData();
      this.captureSnapshot();
    }
  }

  peer: Peer = {} as Peer;

  /** Serialized snapshot of the editable fields as originally loaded. */
  private snapshot = '';

  validationResult!: ServerValidationError;

  @Output() onFinish = new EventEmitter<boolean>();

  constructor(private notification: NotificationService,
    private webapiService: WebapiService,
    private confirmationDialogService: ConfirmationDialogService) {

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

  /** Sorted list of ids from the given related-item array (order-independent). */
  private sortedIds(list: Array<{ id: number }> | undefined): number[] {
    return (list || []).map(x => x.id).sort((a, b) => a - b);
  }

  /** Normalized representation of the user-editable fields. */
  private get editableState(): any {
    return {
      name: this.peer.name,
      description: this.peer.description,
      email_address: this.peer.email_address,
      disabled: this.peer.disabled,
      peer_groups: this.sortedIds(this.peer.peer_groups),
    };
  }

  private captureSnapshot(): void {
    this.snapshot = JSON.stringify(this.editableState);
  }

  /** True when any user-editable field differs from the originally loaded data. */
  get hasChanges(): boolean {
    return JSON.stringify(this.editableState) !== this.snapshot;
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

  sendConfigurationByEmail(event: Event): void {

    this.confirmationDialogService.confirm('Confirm', 'Are you sure you want to send email to ' + this.editItem.name + '?')
      .subscribe(dialogResult => {
        if (dialogResult) {

          this.webapiService.sendConfigurationByEmail(this.peer).subscribe({
            next: data => {
              this.notification.success('e-Mail sent successully.');
            },
            error: error => {
              let response = error as HttpErrorResponse;
              if (response) {
                this.validationResult = response.error as ServerValidationError;
              }
            },
            complete: () => {

            },
          });

        }
      });

  }

}
