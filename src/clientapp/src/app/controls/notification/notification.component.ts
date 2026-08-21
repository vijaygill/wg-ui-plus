import { Component, ChangeDetectionStrategy } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { NotificationService } from '../../services/notification.service';

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
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './notification.component.scss',
})
export class NotificationComponent {

    /** Reactive view of the notification service's current notification. */
    readonly notification = this.notificationService.notification;

    constructor(private notificationService: NotificationService) {
    }

    get icon(): string {
        switch (this.notification()?.type) {
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
        const type = this.notification()?.type;
        return (type === 'success' || type === 'info') ? 'primary' : 'warn';
    }

    onAction(): void {
        this.notification()?.action?.callback();
    }

    dismiss(): void {
        this.notificationService.clear();
    }
}
