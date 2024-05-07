import { Component } from '@angular/core';
import { Peer, WebapiService } from '../webapi.service';
import { MessageService } from 'primeng/api';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PrimeNGModule } from '../primeng.module';
import { CrudContainerComponent } from '../crud-container/crud-container.component';
import { ManagePeersListComponent } from '../manage-peers-list/manage-peers-list.component';
import { ManagePeersEditorComponent } from '../manage-peers-editor/manage-peers-editor.component';

@Component({
  selector: 'app-manage-peers',
  standalone: true,
  imports: [CommonModule, FormsModule, PrimeNGModule, CrudContainerComponent, ManagePeersListComponent, ManagePeersEditorComponent],
  providers: [MessageService],
  templateUrl: './manage-peers.component.html',
  styleUrl: './manage-peers.component.scss'
})
export class ManagePeersComponent {

}
