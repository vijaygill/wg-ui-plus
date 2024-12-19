import { Injectable } from '@angular/core';
import { ConfirmationService, } from 'primeng/api';
import { Observable, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ConfirmationDialogService {

  public dialogResult = new Subject<boolean>();

  constructor(private confirmationService: ConfirmationService) {
  }

  public confirm(title: string, message: string): Observable<boolean> {
    this.confirmationService.confirm({
      header: title,
      message: message,
      accept: () => {
        this.dialogResult.next(true);
      },
      reject: () => {
        this.dialogResult.next(false);
      },
    });
    return this.dialogResult;
  }

  public showMessage(title: string, message: string): Observable<boolean> {
    this.confirmationService.confirm({
      header: title,
      message: message,
      accept: () => {
        this.dialogResult.next(true);
      },
      reject: () => {
        this.dialogResult.next(false);
      },
    });
    return this.dialogResult;
  }
}