import { Component } from '@angular/core';
import { MessageService } from 'primeng/api';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { CrudContainerComponent } from '../crud-container/crud-container.component';
import { ManagePeersListComponent } from '../manage-peers-list/manage-peers-list.component';
import { ManagePeersEditorComponent } from '../manage-peers-editor/manage-peers-editor.component';

@Component({
    standalone: true,
    selector: 'app-manage-peers',
    imports: [CommonModule, FormsModule, AppSharedModule, CrudContainerComponent, ManagePeersListComponent, ManagePeersEditorComponent],
    providers: [MessageService],
    templateUrl: './manage-peers.component.html',
    styleUrl: './manage-peers.component.scss'
})
export class ManagePeersComponent {

}
