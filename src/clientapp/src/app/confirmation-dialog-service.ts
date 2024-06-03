import { Injectable } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Observable } from 'rxjs';
import { ConfirmationDialogComponent, ConfirmationDialogData } from './confirmation-dialog/confirmation-dialog.component';
@Injectable({
  providedIn: 'root',
})
export class ConfirmationDialogService {

  constructor(private dialog: MatDialog) {

  }

  confirm(title: string, message: string): Observable<boolean> {
    const res = this.dialog.open(ConfirmationDialogComponent, {
      maxWidth: "400px",
      data: { title: title, message: message, only_ok: false } as ConfirmationDialogData,
    }).afterClosed();
    return res;
  }

  showMessage(title: string, message: string): Observable<boolean> {
    const res = this.dialog.open(ConfirmationDialogComponent, {
      maxWidth: "400px",
      data: { title: title, message: message, only_ok: true } as ConfirmationDialogData,
    }).afterClosed();
    return res;
  }

}