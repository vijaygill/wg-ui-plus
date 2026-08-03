import { Component, Inject } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MAT_SNACK_BAR_DATA, MatSnackBarModule } from '@angular/material/snack-bar';

export type NotificationType = 'success' | 'error' | 'warn' | 'info';

export interface NotificationData {
    type: NotificationType;
    message: string;
}

/**
 * Content component rendered inside the Material snackbar by NotificationService.
 * Shows a severity-coloured icon alongside the message text.
 */
@Component({
    selector: 'app-notification',
    standalone: true,
    imports: [MatIconModule, MatSnackBarModule],
    templateUrl: './notification.component.html',
    styleUrl: './notification.component.scss',
})
export class NotificationComponent {

    constructor(@Inject(MAT_SNACK_BAR_DATA) public data: NotificationData) { }

    get icon(): string {
        switch (this.data.type) {
            case 'success':
                return 'check_circle';
            case 'error':
                return 'error';
            case 'warn':
                return 'warning';
            case 'info':
            default:
                return 'info';
        }
    }
}
