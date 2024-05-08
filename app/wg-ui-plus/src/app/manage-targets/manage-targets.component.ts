import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { SharedModule } from '../shared.module';
import { CrudContainerComponent } from '../crud-container/crud-container.component';
import { ManageTargetsListComponent } from '../manage-targets-list/manage-targets-list.component';
import { ManageTargetsEditorComponent } from '../manage-targets-editor/manage-targets-editor.component';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-manage-targets',
  standalone: true,
  imports: [CommonModule, FormsModule, SharedModule, CrudContainerComponent,
    ManageTargetsListComponent, ManageTargetsEditorComponent],
  providers: [MessageService],
  templateUrl: './manage-targets.component.html',
  styleUrl: './manage-targets.component.scss'
})
export class ManageTargetsComponent {

}
