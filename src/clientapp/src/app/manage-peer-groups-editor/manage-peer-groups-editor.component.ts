import { Component, EventEmitter, Input, Output, ChangeDetectionStrategy, ChangeDetectorRef, inject } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { HttpErrorResponse } from '@angular/common/http';
import { ValidationErrorsDisplayComponent } from '../validation-errors-display/validation-errors-display.component';
import { ConfirmationDialogService } from '../confirmation-dialog.service';
import { PeerGroup, ServerValidationError, Target } from '../webapi.entities';
import { WebapiService } from '../webapi.service';

@Component({
    standalone: true,
    selector: 'app-manage-peer-groups-editor',
    imports: [FormsModule, AppSharedModule, ValidationErrorsDisplayComponent],
    templateUrl: './manage-peer-groups-editor.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './manage-peer-groups-editor.component.scss'
})
export class ManagePeerGroupsEditorComponent {
  private changeDetectorRef = inject(ChangeDetectorRef);
  @Input()
  get editItem(): PeerGroup { return this.peerGroup; }
  set editItem(value: PeerGroup) {
    this.peerGroup = value;
    this.captureSnapshot();
    if (this.peerGroup.id) {
      this.webapiService.getPeerGroup(value.id).subscribe(data => {
        this.peerGroup = data;
        this.getLookupData();
        this.captureSnapshot();
        this.changeDetectorRef.markForCheck();
      });
    }
    else {
      this.getLookupData();
      this.captureSnapshot();
    }
  }

  peerGroup: PeerGroup = {} as PeerGroup;

  /** Serialized snapshot of the editable fields as originally loaded. */
  private snapshot = '';

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
        this.changeDetectorRef.markForCheck();
      });
      this.webapiService.getTargetList().subscribe(lookup => {
        let lookupItems = this.peerGroup.targets ?
          lookup.filter(x => !this.peerGroup.targets.some(y => y.id === x.id))
          : lookup;
        this.peerGroup.targets_lookup = lookupItems;
        this.changeDetectorRef.markForCheck();
      });
    }
  }

  /** Sorted list of ids from the given related-item array (order-independent). */
  private sortedIds(list: Array<{ id: number }> | undefined): number[] {
    return (list || []).map(x => x.id).sort((a, b) => a - b);
  }

  /** Normalized representation of the user-editable fields. */
  private get editableState(): any {
    return {
      name: this.peerGroup.name,
      description: this.peerGroup.description,
      disabled: this.peerGroup.disabled,
      peers: this.sortedIds(this.peerGroup.peers),
      targets: this.sortedIds(this.peerGroup.targets),
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
    this.webapiService.savePeerGroup(this.peerGroup)
      .subscribe({
        next: data => {
        },
        error: error => {
          let response = error as HttpErrorResponse;
          if (response) {
            this.validationResult = response.error as ServerValidationError;
            this.changeDetectorRef.markForCheck();
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
                  this.changeDetectorRef.markForCheck();
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
