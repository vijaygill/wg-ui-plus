import { Injectable } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ConfirmDialogComponent } from './confirm-dialog/confirm-dialog.component';

@Injectable({
    providedIn: 'root',
})
export class ConfirmationDialogService {

    constructor(private dialog: MatDialog) {
    }

    public confirm(title: string, message: string): Observable<boolean> {
        return this.openDialog(title, message);
    }

    public showMessage(title: string, message: string): Observable<boolean> {
        return this.openDialog(title, message);
    }

    private openDialog(title: string, message: string): Observable<boolean> {
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
            data: { title, message },
        });
        return dialogRef.afterClosed().pipe(
            map((result: boolean | undefined) => result === true)
        );
    }
}
