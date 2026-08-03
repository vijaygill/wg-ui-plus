import { Component, ChangeDetectionStrategy } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { WebapiService } from '../webapi.service';
import { NotificationService } from '../notification.service';
import { ConfirmationDialogService } from '../confirmation-dialog.service';

@Component({
    standalone: true,
    selector: 'app-testpage',
    imports: [FormsModule, AppSharedModule],
    templateUrl: './testpage.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './testpage.component.scss'
})
export class TestpageComponent {

    constructor(private notification: NotificationService,
        private confirmationDialogService: ConfirmationDialogService,
        private webapiService: WebapiService) { }

    ngOnInit() {
        this.refreshData();
    }

    refreshData() {
    }

    showSuccess(): void {
        this.notification.success('This is a success notification.');
    }

    showError(): void {
        this.notification.error('This is an error notification.');
    }

    showWarn(): void {
        this.notification.warn('This is a warning notification.');
    }

    showInfo(): void {
        this.notification.info('This is an info notification.');
    }

    confirmDemo(): void {
        this.confirmationDialogService.confirm('Confirm', 'Do you want to continue?').subscribe(ok => {
            if (ok) {
                this.notification.success('You confirmed the action.');
            } else {
                this.notification.info('You cancelled the action.');
            }
        });
    }

    showMessageDemo(): void {
        this.confirmationDialogService.showMessage('Information', 'This is an informational message.').subscribe(() => {
        });
    }
}
