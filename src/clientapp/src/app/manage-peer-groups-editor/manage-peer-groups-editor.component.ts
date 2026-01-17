import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { AppSharedModule } from '../app-shared.module';
import { HttpErrorResponse } from '@angular/common/http';
import { ValidationErrorsDisplayComponent } from '../validation-errors-display/validation-errors-display.component';
import { ConfirmationDialogService } from '../confirmation-dialog-service';
import { PeerGroup, ServerValidationError, Target } from '../webapi.entities';
import { WebapiService } from '../webapi.service';

@Component({
    standalone: true,
    changeDetection: ChangeDetectionStrategy.OnPush,
    selector: 'app-manage-peer-groups-editor',
    imports: [FormsModule, AppSharedModule, ValidationErrorsDisplayComponent],
    providers: [MessageService, ConfirmationDialogService],
    templateUrl: './manage-peer-groups-editor.component.html',
    styleUrl: './manage-peer-groups-editor.component.scss'
})
export class ManagePeerGroupsEditorComponent {
  @Input()
  get editItem(): PeerGroup { return this.peerGroup; }
  set editItem(value: PeerGroup) {
    this.peerGroup = value;
    if (this.peerGroup.id) {
      this.webapiService.getPeerGroup(value.id).subscribe(data => {
        this.peerGroup = data;
        this.getLookupData();
      });
    }
    else {
      this.getLookupData();
    }
  }

  peerGroup: PeerGroup = {} as PeerGroup;

  validationResult!: ServerValidationError;

  @Output() onFinish = new EventEmitter<boolean>();

  constructor(private webapiService: WebapiService,
    private confirmationDialogService: ConfirmationDialogService) { }

  getLookupData() {
    if (this.peerGroup) {
      this.webapiService.getPeerList().subscribe(lookup => {
        let lookupItems = this.peerGroup.peers ?
          lookup.filter(x => !this.peerGroup.peers.some(y => y.id === x.id))
          : lookup;
        this.peerGroup.peers_lookup = lookupItems;
      });
      this.webapiService.getTargetList().subscribe(lookup => {
        let lookupItems = this.peerGroup.targets ?
          lookup.filter(x => !this.peerGroup.targets.some(y => y.id === x.id))
          : lookup;
        this.peerGroup.targets_lookup = lookupItems;
      });
    }
  }

  ok() {
    this.webapiService.savePeerGroup(this.peerGroup)
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

  delete(event: Event) {
    if (!this.peerGroup) {
      return;
    }

    this.confirmationDialogService.confirm('Confirm', 'Are you sure that you want to delete ' + this.editItem.name + '?')
      .subscribe(dialogResult => {
        if (dialogResult) {
          this.webapiService.deletePeerGroup(this.peerGroup)
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

  cancel() {
    this.onFinish.emit(false);
  }
}
