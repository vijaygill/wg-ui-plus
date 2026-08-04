
import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { ServerValidationError } from '../../webapi.entities';
import { MatIconModule } from '@angular/material/icon';

export interface ValidationErrorMessage {
    severity: string;
    detail: string;
}

@Component({
    standalone: true,
    selector: 'app-validation-errors-display',
    imports: [MatIconModule],
    templateUrl: './validation-errors-display.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './validation-errors-display.component.scss'
})
export class ValidationErrorsDisplayComponent {
  @Input() field!: string;
  @Input() validationResult!: ServerValidationError;

  errorList(): ValidationErrorMessage[] {
    let res: ValidationErrorMessage [] = [];
    if (this.validationResult && this.validationResult.errors) {
      this.validationResult.errors.forEach(validationResultItem => {
        let createMessage = !this.field || this.field == validationResultItem.attr;
        if (!createMessage) {
          return;
        }
        if (!validationResultItem.detail) {
          return;
        }
        let message = { severity: 'error', detail: validationResultItem.detail } as ValidationErrorMessage;
        res.push(message);
      }
      );
    }
    return res;
  }

}
