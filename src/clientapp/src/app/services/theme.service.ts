import { Injectable } from '@angular/core';

export type AppTheme = 'dark' | 'light';

const THEME_STORAGE_KEY = 'wg-ui-plus-theme';

/**
 * Manages the app-wide light/dark Material 3 theme.
 *
 * The active theme is persisted to localStorage and applied as a `light` or
 * `dark` class on the document root (`<html>`). Defaults to dark, falling back
 * to the user's `prefers-color-scheme` preference when nothing is stored.
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {

    private _theme: AppTheme = 'dark';

    constructor() {
        this._theme = this.detectInitialTheme();
        this.apply();
    }

    get theme(): AppTheme {
        return this._theme;
    }

    get isDark(): boolean {
        return this._theme === 'dark';
    }

    get isLight(): boolean {
        return this._theme === 'light';
    }

    /** Toggle between light and dark, applying + persisting the result. */
    toggle(): AppTheme {
        this.set(this._theme === 'dark' ? 'light' : 'dark');
        return this._theme;
    }

    /** Set the theme explicitly, applying + persisting it. */
    set(theme: AppTheme): void {
        this._theme = theme;
        this.persist();
        this.apply();
    }

    private detectInitialTheme(): AppTheme {
        let stored: string | null = null;
        try {
            stored = localStorage.getItem(THEME_STORAGE_KEY);
        } catch {
            // Ignore storage failures (e.g. private browsing); fall through to
            // the OS-preference / default fallbacks below.
            stored = null;
        }
        if (stored === 'light' || stored === 'dark') {
            return stored;
        }
        if (typeof window.matchMedia === 'function'
            && window.matchMedia('(prefers-color-scheme: light)').matches) {
            return 'light';
        }
        return 'dark';
    }

    private persist(): void {
        try {
            localStorage.setItem(THEME_STORAGE_KEY, this._theme);
        } catch {
            // Ignore storage failures (e.g. private browsing); still apply the theme.
        }
    }

    private apply(): void {
        const root = document.documentElement;
        root.classList.remove('light', 'dark');
        root.classList.add(this._theme);
    }
}
