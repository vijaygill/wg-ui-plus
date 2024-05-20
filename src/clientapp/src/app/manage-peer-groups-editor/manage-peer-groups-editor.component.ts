import { Component, EventEmitter, Input, Output } from '@angular/core';
import { PeerGroup, ServerValidationError, Target, WebapiService } from '../webapi.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { AppSharedModule } from '../app-shared.module';
import { HttpErrorResponse } from '@angular/common/http';
import { ValidationErrorsDisplayComponent } from '../validation-errors-display/validation-errors-display.component';

@Component({
  selector: 'app-manage-peer-groups-editor',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule, ValidationErrorsDisplayComponent],
  providers: [MessageService],
  templateUrl: './manage-peer-groups-editor.component.html',
  styleUrl: './manage-peer-groups-editor.component.scss'
})
export class ManagePeerGroupsEditorComponent {
  @Input()
  get editItem(): PeerGroup { return this.peerGroup; }
  set editItem(value: PeerGroup) {
    this.peerGroup = value;
    this.webapiService.getPeerGroup(value.id).subscribe(data => {
      this.peerGroup = data;
    });
  }

  peerGroup: PeerGroup = {} as PeerGroup;

  validationResult!: ServerValidationError;

  @Output() onFinish = new EventEmitter<boolean>();

  constructor(private messageService: MessageService, private webapiService: WebapiService) { }

  ngOnInit() {
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
