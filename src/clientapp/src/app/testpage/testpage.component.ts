import { ChangeDetectionStrategy, Component } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { AppSharedModule } from '../app-shared.module';
import { WebapiService } from '../webapi.service';

@Component({
    standalone: true,
    changeDetection: ChangeDetectionStrategy.OnPush,
    selector: 'app-testpage',
    imports: [FormsModule, AppSharedModule],
    providers: [MessageService],
    templateUrl: './testpage.component.html',
    styleUrl: './testpage.component.scss'
})
export class TestpageComponent {

    constructor(private messageService: MessageService, private webapiService: WebapiService) { }

    ngOnInit() {
        this.refreshData();
    }

    refreshData() {
    }

   
}
