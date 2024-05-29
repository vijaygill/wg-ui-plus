import { Component, EventEmitter, Input, Output } from '@angular/core';
import { PeerGroup, ServerValidationError, Target, WebapiService } from '../webapi.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ConfirmationService, MessageService } from 'primeng/api';
import { AppSharedModule } from '../app-shared.module';
import { HttpErrorResponse } from '@angular/common/http';
import { ValidationErrorsDisplayComponent } from '../validation-errors-display/validation-errors-display.component';
import { ConfirmDialogModel, ConfirmationDialogComponent } from '../confirmation-dialog/confirmation-dialog.component';
import { MatDialog } from '@angular/material/dialog';

@Component({
  selector: 'app-manage-peer-groups-editor',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule, ValidationErrorsDisplayComponent],
  providers: [ConfirmationService, MessageService],
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

  constructor(private messageService: MessageService,
    private confirmationService: ConfirmationService,
    private webapiService: WebapiService,
    public dialog: MatDialog) { }

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

    const dialogData = new ConfirmDialogModel("Confirm Action", 'Are you sure that you want to proceed?');
    const dialogRef = this.dialog.open(ConfirmationDialogComponent, {
      maxWidth: "400px",
      data: dialogData
    });

    dialogRef.afterClosed().subscribe(dialogResult => {
      alert('boo!');
    });

    return;

    this.confirmationService.confirm({
      target: event.target as EventTarget,
      message: 'Are you sure that you want to proceed?',
      header: 'Confirmation',
      icon: 'pi pi-exclamation-triangle',
      acceptIcon: "none",
      rejectIcon: "none",
      rejectButtonStyleClass: "p-button-text",
      accept: () => {
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
      },
      reject: () => {
      }
    });

  }

  cancel() {
    this.onFinish.emit(false);
  }

  peersPickListTrackBy(index: number, item: any) {
    let x = item as PeerGroup;
    return x.id;
  }

  targetsPickListTrackBy(index: number, item: any) {
    let x = item as Target;
    return x.id;
  }
}
