import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { PrimeNGModule } from '../primeng.module';
import { CrudContainerComponent } from '../crud-container/crud-container.component';
import { ManageTargetGroupsListComponent } from '../manage-target-groups-list/manage-target-groups-list.component';
import { MessageService } from 'primeng/api';
import { ManageTargetGroupsEditorComponent } from '../manage-target-groups-editor/manage-target-groups-editor.component';

@Component({
  selector: 'app-manage-target-groups',
  standalone: true,
  imports: [CommonModule, FormsModule, PrimeNGModule, CrudContainerComponent,
    ManageTargetGroupsListComponent, ManageTargetGroupsEditorComponent],
  providers: [MessageService],
  templateUrl: './manage-target-groups.component.html',
  styleUrl: './manage-target-groups.component.scss'
})
export class ManageTargetGroupsComponent {

}
