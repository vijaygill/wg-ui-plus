import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export type NotificationType = 'success' | 'error' | 'warn' | 'info';

export interface NotificationAction {
    label: string;
    callback: () => void;
}

export interface AppNotification {
    type: NotificationType;
    message: string;
    /** Optional button shown in the banner (e.g. "Apply Changes"). */
    action?: NotificationAction;
    /** Persistent messages stay until cleared/replaced; transient ones auto-dismiss. */
    persistent?: boolean;
    /** If true, a dismiss (X) button is shown. No current notification sets this. */
    dismissible?: boolean;
}

/**
 * Single, unified notification surface rendered as an inline banner at the top
 * of the content area (see NotificationComponent).
 *
 * One message is shown at a time. Persistent messages (server offline, mandatory
 * actions) win over transient feedback (success/info), so important state is
 * never hidden by a short-lived toast. Transient messages auto-dismiss.
 */
@Injectable({ providedIn: 'root' })
export class NotificationService {

    private readonly durationMs = 4000;
    private readonly current$ = new BehaviorSubject<AppNotification | null>(null);
    private current: AppNotification | null = null;
    private autoDismissTimer: ReturnType<typeof setTimeout> | null = null;

    public readonly notification$: Observable<AppNotification | null> = this.current$.asObservable();

    public success(message: string): void {
        this.show({ type: 'success', message });
    }

    public error(message: string): void {
        this.show({ type: 'error', message });
    }

    public warn(message: string): void {
        this.show({ type: 'warn', message });
    }

    public info(message: string): void {
        this.show({ type: 'info', message });
    }

    public show(notification: AppNotification): void {
        // A transient (auto-dismissing) message must never replace a persistent
        // one — important state stays visible until it is cleared or replaced.
        if (this.current && this.current.persistent && !notification.persistent) {
            return;
        }
        this.clearTimer();
        this.current = notification;
        this.current$.next(notification);
        if (!notification.persistent) {
            this.autoDismissTimer = setTimeout(() => this.clear(), this.durationMs);
        }
    }

    public clear(): void {
        this.clearTimer();
        this.current = null;
        this.current$.next(null);
    }

    private clearTimer(): void {
        if (this.autoDismissTimer !== null) {
            clearTimeout(this.autoDismissTimer);
            this.autoDismissTimer = null;
        }
    }
}
