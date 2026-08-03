import { Component, OnDestroy } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subscription } from 'rxjs';
import { AppNotification, NotificationService } from '../notification.service';

/**
 * Unified notification banner rendered at the top of the content area by
 * app.component. Shows the current notification (from NotificationService):
 * severity icon + message + optional action button + optional dismiss (X).
 */
@Component({
    selector: 'app-notification',
    standalone: true,
    imports: [MatIconModule, MatButtonModule, MatTooltipModule],
    templateUrl: './notification.component.html',
    styleUrl: './notification.component.scss',
})
export class NotificationComponent implements OnDestroy {

    notification: AppNotification | null = null;

    private subscription: Subscription;

    constructor(private notificationService: NotificationService) {
        this.subscription = this.notificationService.notification$.subscribe(
            (notification) => this.notification = notification
        );
    }

    ngOnDestroy(): void {
        this.subscription.unsubscribe();
    }

    get icon(): string {
        switch (this.notification?.type) {
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

    get actionColor(): string {
        return (this.notification?.type === 'success' || this.notification?.type === 'info') ? 'primary' : 'warn';
    }

    onAction(): void {
        this.notification?.action?.callback();
    }

    dismiss(): void {
        this.notificationService.clear();
    }
}
