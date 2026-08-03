import { Injectable } from '@angular/core';
import { MatSnackBar, MatSnackBarRef } from '@angular/material/snack-bar';
import { NotificationComponent, NotificationData, NotificationType } from './notification/notification.component';

export { NotificationComponent, NotificationData, NotificationType } from './notification/notification.component';

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
