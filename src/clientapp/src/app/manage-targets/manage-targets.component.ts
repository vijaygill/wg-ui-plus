
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { CrudContainerComponent } from '../crud-container/crud-container.component';
import { ManageTargetsListComponent } from '../manage-targets-list/manage-targets-list.component';
import { ManageTargetsEditorComponent } from '../manage-targets-editor/manage-targets-editor.component';
import { MessageService } from 'primeng/api';

@Component({
    standalone: true,
    selector: 'app-manage-targets',
    imports: [FormsModule, AppSharedModule, CrudContainerComponent, ManageTargetsListComponent, ManageTargetsEditorComponent],
    providers: [MessageService],
    templateUrl: './manage-targets.component.html',
    styleUrl: './manage-targets.component.scss'
})
export class ManageTargetsComponent {

}
