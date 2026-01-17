import { ChangeDetectionStrategy, Component, EventEmitter, Input, Output } from '@angular/core';
import { MessageService } from 'primeng/api';

import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { Peer, PeerGroup, Target } from '../webapi.entities';
import { WebapiService } from '../webapi.service';

@Component({
    standalone: true,
    changeDetection: ChangeDetectionStrategy.OnPush,
    selector: 'app-manage-peer-groups-list',
    imports: [FormsModule, AppSharedModule],
    providers: [MessageService],
    templateUrl: './manage-peer-groups-list.component.html',
    styleUrl: './manage-peer-groups-list.component.scss'
})
export class ManagePeerGroupsListComponent {
  peerGroups: PeerGroup[] = [];

  constructor(private messageService: MessageService, private webapiService: WebapiService) { }

  ngOnInit() {
    this.refreshData();
  }

  refreshData(): void {
    this.webapiService.getPeerGroupList().subscribe(data => {
      this.peerGroups = data;
    });
  }

  @Output() onNewItem = new EventEmitter<PeerGroup>();
  @Output() onEdit = new EventEmitter<PeerGroup>();

  newItem(): void {
    if (this.onNewItem) {
      let peerGroup = {
        allow_modify_peers: true,
        allow_modify_targets: true,
        allow_modify_self: true,
        peer_ids: [] as number[],
        peers: [] as Peer[],
        target_ids: [] as number[],
        targets : [] as Target[],
      } as PeerGroup;
      this.onNewItem.emit(peerGroup);
    }
  }

  editItem(peerGroup: PeerGroup): void {
    if (this.onEdit) {
      this.onEdit.emit(peerGroup);
    }
  }
}
