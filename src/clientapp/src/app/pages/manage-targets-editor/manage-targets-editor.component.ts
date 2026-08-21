import { Component, EventEmitter, Input, Output, ChangeDetectionStrategy, signal } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../../app-shared.module';
import { HttpErrorResponse } from '@angular/common/http';
import { ValidationErrorsDisplayComponent } from '../../controls/validation-errors-display/validation-errors-display.component';
import { ConfirmationDialogService } from '../../services/confirmation-dialog.service';
import { PeerGroup, ServerValidationError, Target } from '../../webapi.entities';
import { WebapiService } from '../../services/webapi.service';

@Component({
    standalone: true,
    selector: 'app-manage-targets-editor',
    imports: [FormsModule, AppSharedModule, ValidationErrorsDisplayComponent],
    templateUrl: './manage-targets-editor.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './manage-targets-editor.component.scss'
})
export class ManageTargetsEditorComponent {
  @Input()
  get editItem(): Target { return this.targetSignal(); }
  set editItem(value: Target) {
    this.targetSignal.set(value);
    this.captureSnapshot();
    if (this.target.id) {
      this.webapiService.getTarget(value.id).subscribe(data => {
        this.targetSignal.set(data);
        this.getLookupData();
        this.captureSnapshot();
      });
    }
    else {
      this.getLookupData();
      this.captureSnapshot();
    }
  }

  private targetSignal = signal<Target>({} as Target);

  /** Preserves the former field name for all internal read sites. */
  private get target(): Target { return this.targetSignal(); }

  /** Serialized snapshot of the editable fields as originally loaded. */
  private snapshot = '';

  validationResult = signal<any | undefined>(undefined);

  @Output() onFinish = new EventEmitter<boolean>();

  constructor(private webapiService: WebapiService,
    private confirmationDialogService: ConfirmationDialogService) { }

  getLookupData() {
    this.webapiService.getPeerGroupList().subscribe(lookup => {
      let lookupItems = this.target.peer_groups ?
        lookup.filter(x => !this.target.peer_groups.some(y => y.id === x.id) && !x.is_everyone_group)
        : lookup;
      this.targetSignal.update(target => ({ ...target, peer_groups_lookup: lookupItems }));
    });
  }

  /** Sorted list of ids from the given related-item array (order-independent). */
  private sortedIds(list: Array<{ id: number }> | undefined): number[] {
    return (list || []).map(x => x.id).sort((a, b) => a - b);
  }

  /** Normalized representation of the user-editable fields. */
  private get editableState(): any {
    return {
      name: this.target.name,
      description: this.target.description,
      ip_address: this.target.ip_address,
      disabled: this.target.disabled,
      peer_groups: this.sortedIds(this.target.peer_groups),
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
    this.webapiService.saveTarget(this.target)
      .subscribe({
        next: data => {
        },
        error: error => {
          let response = error as HttpErrorResponse;
          if (response) {
            this.validationResult.set(response.error);
          }
        },
        complete: () => {
          this.onFinish.emit(true);
        },
      });
  }

  delete(event: Event) {
    if (!this.target) {
      return;
    }

    this.confirmationDialogService.confirm('Confirm', 'Are you sure that you want to delete ' + this.editItem.name + '?')
      .subscribe(dialogResult => {
        if (dialogResult) {
          this.webapiService.deleteTarget(this.target)
            .subscribe({
              next: data => {
              },
              error: error => {
                let response = error as HttpErrorResponse;
                if (response) {
                  this.validationResult.set(response.error as ServerValidationError);
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
