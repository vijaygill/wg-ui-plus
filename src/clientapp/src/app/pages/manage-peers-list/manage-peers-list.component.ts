import { Component, EventEmitter, Output, ChangeDetectionStrategy } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../../app-shared.module';
import { Sort } from '@angular/material/sort';
import { Peer, PeerGroup } from '../../webapi.entities';
import { WebapiService } from '../../services/webapi.service';

@Component({
    standalone: true,
    selector: 'app-manage-peers-list',
    imports: [FormsModule, AppSharedModule],
    templateUrl: './manage-peers-list.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './manage-peers-list.component.scss'
})
export class ManagePeersListComponent {
  peers: Peer[] = [];
  private currentSort: Sort = { active: 'name', direction: 'asc' };

  constructor(private webapiService: WebapiService) { }

  ngOnInit() {
    this.refreshData();
  }

  refreshData(): void {
    this.webapiService.getPeerList().subscribe(data => {
      this.peers = data;
      // Preserve the default sort (by name, ascending) on first load,
      // matching the original sortField="name" behaviour.
      this.sortData(this.currentSort);
    });
  }

  @Output() onNewItem = new EventEmitter<Peer>();
  @Output() onEdit = new EventEmitter<Peer>();

  newItem(): void {
    if (this.onNewItem) {
      let peer = {
        peer_group_ids: [] as number[],
        peer_groups: [] as PeerGroup[],
      } as Peer;
      this.onNewItem.emit(peer);
    }
  }

  editItem(peer: Peer): void {
    if (this.onEdit) {
      this.onEdit.emit(peer);
    }
  }

  sortData(sort: Sort): void {
    this.currentSort = sort;
    if (!sort.active || sort.direction === '') {
      return;
    }
    const sorted = [...this.peers].sort((a, b) => {
      const aValue = String((a as any)[sort.active] ?? '');
      const bValue = String((b as any)[sort.active] ?? '');
      const cmp = aValue.localeCompare(bValue);
      return sort.direction === 'asc' ? cmp : -cmp;
    });
    this.peers = sorted;
  }
}
