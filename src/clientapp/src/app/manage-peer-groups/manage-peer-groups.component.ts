import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { ManagePeerGroupsListComponent } from '../manage-peer-groups-list/manage-peer-groups-list.component';
import { ManagePeerGroupsEditorComponent } from '../manage-peer-groups-editor/manage-peer-groups-editor.component';
import { CrudContainerComponent } from '../crud-container/crud-container.component';
import { MessageService } from 'primeng/api';

@Component({
    standalone: true,
    selector: 'app-manage-peer-groups',
    imports: [CommonModule, FormsModule, AppSharedModule,
        CrudContainerComponent,
        ManagePeerGroupsListComponent, ManagePeerGroupsEditorComponent],
    providers: [MessageService],
    templateUrl: './manage-peer-groups.component.html',
    styleUrl: './manage-peer-groups.component.scss'
})
export class ManagePeerGroupsComponent {
}
