import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogActions, MatDialogContent, MatDialogRef, MatDialogTitle } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';

@Component({
    standalone: true,
    selector: 'app-confirmation-dialog',
    imports: [CommonModule, MatButtonModule, MatDialogActions, MatDialogTitle, MatDialogContent,],
    templateUrl: './confirmation-dialog.component.html',
    styleUrl: './confirmation-dialog.component.scss'
})
export class ConfirmationDialogComponent {

  data: ConfirmationDialogData = {
    title: 'No title',
    message: 'No message',
  } as ConfirmationDialogData;

  constructor(public dialogRef: MatDialogRef<ConfirmationDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public dialogData: ConfirmationDialogData) {
    this.data = dialogData;
  }

  onConfirm(): void {
    this.dialogRef.close(true);
  }

  onDismiss(): void {
    this.dialogRef.close(false);
  }
}

export interface ConfirmationDialogData {
  title: string;
  message: string;
  only_ok: boolean;
}

