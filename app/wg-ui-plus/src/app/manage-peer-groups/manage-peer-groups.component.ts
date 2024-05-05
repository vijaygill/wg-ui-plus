import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PrimeNGModule } from '../primeng.module';
import { ManagePeerGroupsListComponent } from '../manage-peer-groups-list/manage-peer-groups-list.component';
import { ManagePeerGroupsEditorComponent } from '../manage-peer-groups-editor/manage-peer-groups-editor.component';
import { PeerGroup } from '../webapi.service';

@Component({
  selector: 'app-manage-peer-groups',
  standalone: true,
  imports: [CommonModule, FormsModule, PrimeNGModule,
    ManagePeerGroupsListComponent, ManagePeerGroupsEditorComponent],
  providers: [],
  templateUrl: './manage-peer-groups.component.html',
  styleUrl: './manage-peer-groups.component.scss'
})
export class ManagePeerGroupsComponent {
  showEditor: boolean = false;
  editItem: PeerGroup = { id: 0, name: '' };

  onEditItem(peerGroup: PeerGroup) {
    this.editItem = peerGroup;
    this.showEditor = true;
  }

  onEditFinish(editorResult: boolean)
  {
    this.showEditor = false;
  }
}
