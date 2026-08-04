import { Component, Input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';

/**
 * Reusable consistent page header used at the top of every routed page.
 *
 * Renders an optional title + subtitle on the left and an `<ng-content>`
 * projection slot on the right for action buttons.
 */
@Component({
    selector: 'app-page-header',
    standalone: true,
    imports: [CommonModule],
    changeDetection: ChangeDetectionStrategy.OnPush,
    templateUrl: './page-header.component.html',
    styleUrl: './page-header.component.scss',
})
export class PageHeaderComponent {
    @Input() title?: string;
    @Input() subtitle?: string;
}
