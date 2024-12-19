import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { MessagesModule } from 'primeng/messages';
import { ServerValidationError } from '../webapi.entities';
import { ToastMessageOptions } from 'primeng/api';

@Component({
    standalone: true,
    selector: 'app-validation-errors-display',
    imports: [CommonModule, MessagesModule],
    templateUrl: './validation-errors-display.component.html',
    styleUrl: './validation-errors-display.component.scss'
})
export class ValidationErrorsDisplayComponent {
  @Input() field!: string;
  @Input() validationResult!: ServerValidationError;

  errorList(): ToastMessageOptions[] {
    let res: ToastMessageOptions [] = [];
    if (this.validationResult && this.validationResult.errors) {
      this.validationResult.errors.forEach(validationResultItem => {
        let createMessage = !this.field || this.field == validationResultItem.attr;
        if (!createMessage) {
          return;
        }
        if (!validationResultItem.detail) {
          return;
        }
        // let severity = 'error' == validationResultItem.type ? 'error'
        //   : 'warning' == validationResultItem.type ? 'warn'
        //     : 'info';
        let severity = 'error';
        let message = { severity: severity, detail: validationResultItem.detail } as ToastMessageOptions ;
        res.push(message);
      }
      );
    }
    return res;
  }

}

