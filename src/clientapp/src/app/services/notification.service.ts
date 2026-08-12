import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export type NotificationType = 'success' | 'error' | 'warn' | 'info';
export type NotificationSource = 'status' | 'user';

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
    /** If true, a dismiss (X) button is shown. */
    dismissible?: boolean;
    /** Identifies notifications owned by the server-status synchronizer. */
    source?: NotificationSource;
}

interface ShowOptions {
    /** Allows focused user feedback to replace a persistent status notification. */
    replacePersistent?: boolean;
    /** Overrides the default transient notification duration for focused feedback. */
    durationMs?: number;
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
    private readonly emailFailureDurationMs = 15000;
    private readonly current$ = new BehaviorSubject<AppNotification | null>(null);
    private current: AppNotification | null = null;
    private statusNotification: AppNotification | null = null;
    private emailFailureVisible = false;
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

    /**
     * Shows an email failure even when a persistent status banner is active.
     * The displaced status is retained and restored when this message ends.
     */
    public showEmailDeliveryFailure(message: string): void {
        if (this.current?.persistent && this.current.source === 'status') {
            this.statusNotification = this.current;
        }
        this.emailFailureVisible = true;
        this.show(
            { type: 'error', message, dismissible: true, source: 'user' },
            { replacePersistent: true, durationMs: this.emailFailureDurationMs },
        );
    }

    /** Shows or refreshes the latest notification owned by the status synchronizer. */
    public showStatus(notification: AppNotification): void {
        const statusNotification = { ...notification, source: 'status' as const };
        this.statusNotification = statusNotification;
        if (this.emailFailureVisible) {
            return;
        }
        this.show(statusNotification);
    }

    public show(notification: AppNotification, options: ShowOptions = {}): void {
        // A transient (auto-dismissing) message must never replace a persistent
        // one unless the caller has explicitly opted into that focused behavior.
        if (this.current && this.current.persistent && !notification.persistent && !options.replacePersistent) {
            return;
        }
        this.clearTimer();
        this.current = notification;
        this.current$.next(notification);
        if (!notification.persistent) {
            const duration = options.durationMs ?? this.durationMs;
            this.autoDismissTimer = setTimeout(() => this.clear(), duration);
        }
    }

    public isEmailDeliveryFailureVisible(): boolean {
        return this.emailFailureVisible;
    }

    /** Clears a status banner without removing user feedback shown in its place. */
    public clearStatus(): void {
        this.statusNotification = null;
        if (this.current?.source === 'status') {
            this.clear();
        }
    }

    public clear(): void {
        this.clearTimer();
        if (this.emailFailureVisible && this.current?.source === 'user') {
            this.emailFailureVisible = false;
            if (this.statusNotification) {
                this.show(this.statusNotification);
                return;
            }
        }
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
