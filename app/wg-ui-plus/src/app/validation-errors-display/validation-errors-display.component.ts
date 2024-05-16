import { CommonModule } from '@angular/common';
import { Component, ContentChild, Input, OnInit, TemplateRef } from '@angular/core';
import { Message } from 'primeng/api';
import { MessagesModule } from 'primeng/messages';
import { ValidationResultItem } from '../webapi.service';

@Component({
  selector: 'app-validation-errors-display',
  standalone: true,
  imports: [CommonModule, MessagesModule],
  templateUrl: './validation-errors-display.component.html',
  styleUrl: './validation-errors-display.component.scss'
})
export class ValidationErrorsDisplayComponent {
  @Input() field!: string;
  @Input() validationResult!: ValidationResultItem[];

  errorList(): Message[] {
    let res: Message[] = [];
    if (this.validationResult) {
      this.validationResult.forEach(validationResultItem => {
        let createMessage = !this.field || this.field == validationResultItem.field;
        if (!createMessage) {
          return;
        }
        if (!validationResultItem.message) {
          return;
        }
        let severity = 'error' == validationResultItem.type ? 'error'
          : 'warning' == validationResultItem.type ? 'warn'
            : 'info';
        let message = { severity: severity, detail: validationResultItem.message } as Message;
        res.push(message);
      }
      );
    }
    return res;
  }

}

