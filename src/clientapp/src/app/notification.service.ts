import { Component, Inject, Injectable } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MAT_SNACK_BAR_DATA, MatSnackBar, MatSnackBarModule, MatSnackBarRef } from '@angular/material/snack-bar';

export type NotificationType = 'success' | 'error' | 'warn' | 'info';

interface NotificationData {
    type: NotificationType;
    message: string;
}

@Component({
    selector: 'app-notification',
    standalone: true,
    imports: [MatIconModule, MatSnackBarModule],
    template: `
        <div class="snackbar-{{ data.type }}">
            <mat-icon>{{ icon }}</mat-icon>
            <span>{{ data.message }}</span>
        </div>
    `,
    styles: [`
        :host {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        mat-icon {
            flex-shrink: 0;
        }
    `],
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
                return 'info';
            default:
                return 'info';
        }
    }
}

/**
 * Material-native replacement for the old toast pattern.
 *
 * Shows one snackbar at a time (bottom of the screen) and keeps a small FIFO
 * queue of pending messages. Each snackbar auto-dismisses after ~4s and the
 * next queued message is shown afterwards.
 *
 * "Replace current" semantics (used by the periodic server-status refresh):
 * call `clear()` followed by `success()`/`error()`/... to dismiss whatever is
 * showing and drop any queued messages before showing the new one.
 */
@Injectable({ providedIn: 'root' })
export class NotificationService {

    private readonly durationMs = 4000;
    private readonly queue: NotificationData[] = [];
    private current: MatSnackBarRef<NotificationComponent> | null = null;

    constructor(private snackBar: MatSnackBar) { }

    public success(message: string): void {
        this.show('success', message);
    }

    public error(message: string): void {
        this.show('error', message);
    }

    public warn(message: string): void {
        this.show('warn', message);
    }

    public info(message: string): void {
        this.show('info', message);
    }

    public clear(): void {
        this.queue.length = 0;
        if (this.current) {
            this.current.dismiss();
            this.current = null;
        }
    }

    private show(type: NotificationType, message: string): void {
        this.queue.push({ type, message });
        this.displayNext();
    }

    private displayNext(): void {
        if (this.current) {
            return;
        }
        const next = this.queue.shift();
        if (!next) {
            return;
        }
        const ref = this.snackBar.openFromComponent(NotificationComponent, {
            data: next,
            panelClass: 'notification-snackbar',
            duration: this.durationMs,
        });
        this.current = ref;
        ref.afterDismissed().subscribe(() => {
            // Only advance the queue when the dismissal belongs to the snackbar
            // that is currently tracked. This guards against a stale dismissal
            // from a snackbar that was replaced via clear() + show().
            if (this.current === ref) {
                this.current = null;
            }
            this.displayNext();
        });
    }
}
