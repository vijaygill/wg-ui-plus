import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { AppSharedModule } from '../app-shared.module';
import { WebapiService } from '../webapi.service';

@Component({
    standalone: true,
    selector: 'app-testpage',
    imports: [CommonModule, FormsModule, AppSharedModule],
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
