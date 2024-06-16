import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { Message } from 'primeng/api';
import { MessagesModule } from 'primeng/messages';
import { ServerValidationError } from '../webapi.entities';

@Component({
  selector: 'app-validation-errors-display',
  standalone: true,
  imports: [CommonModule, MessagesModule],
  templateUrl: './validation-errors-display.component.html',
  styleUrl: './validation-errors-display.component.scss'
})
export class ValidationErrorsDisplayComponent {
  @Input() field!: string;
  @Input() validationResult!: ServerValidationError;

  errorList(): Message[] {
    let res: Message[] = [];
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
        let message = { severity: severity, detail: validationResultItem.detail } as Message;
        res.push(message);
      }
      );
    }
    return res;
  }

}

