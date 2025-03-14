import { Component, EventEmitter, Input, Output } from '@angular/core';
import { MessageService } from 'primeng/api';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { HttpErrorResponse } from '@angular/common/http';
import { ValidationErrorsDisplayComponent } from '../validation-errors-display/validation-errors-display.component';
import { ConfirmationDialogService } from '../confirmation-dialog-service';
import { PeerGroup, ServerValidationError, Target } from '../webapi.entities';
import { WebapiService } from '../webapi.service';

@Component({
    standalone: true,
    selector: 'app-manage-targets-editor',
    imports: [CommonModule, FormsModule, AppSharedModule, ValidationErrorsDisplayComponent],
    providers: [MessageService, ConfirmationDialogService],
    templateUrl: './manage-targets-editor.component.html',
    styleUrl: './manage-targets-editor.component.scss'
})
export class ManageTargetsEditorComponent {
  @Input()
  get editItem(): Target { return this.target; }
  set editItem(value: Target) {
    this.target = value;
    if (this.target.id) {
      this.webapiService.getTarget(value.id).subscribe(data => {
        this.target = data;
        this.getLookupData();
      });
    }
    else {
      this.getLookupData();
    }
  }

  target: Target = {} as Target;

  validationResult!: any;

  @Output() onFinish = new EventEmitter<boolean>();

  constructor(private messageService: MessageService,
    private webapiService: WebapiService,
    private confirmationDialogService: ConfirmationDialogService) { }

  getLookupData() {
    this.webapiService.getPeerGroupList().subscribe(lookup => {
      let lookupItems = this.target.peer_groups ?
        lookup.filter(x => !this.target.peer_groups.some(y => y.id === x.id) && !x.is_everyone_group)
        : lookup;
      this.target.peer_groups_lookup = lookupItems;
    });
  }

  ok() {
    this.webapiService.saveTarget(this.target)
      .subscribe({
        next: data => {
        },
        error: error => {
          let response = error as HttpErrorResponse;
          if (response) {
            this.validationResult = response.error;
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
