import { Component, EventEmitter, Input, Output, ChangeDetectionStrategy, ChangeDetectorRef } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../../app-shared.module';
import { Sort } from '@angular/material/sort';
import { Peer, PeerGroup, Target } from '../../webapi.entities';
import { WebapiService } from '../../services/webapi.service';

@Component({
    standalone: true,
    selector: 'app-manage-peer-groups-list',
    imports: [FormsModule, AppSharedModule],
    templateUrl: './manage-peer-groups-list.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './manage-peer-groups-list.component.scss'
})
export class ManagePeerGroupsListComponent {
  peerGroups: PeerGroup[] = [];
  private currentSort: Sort = { active: 'name', direction: 'asc' };

  constructor(private webapiService: WebapiService, private cdr: ChangeDetectorRef) { }

  ngOnInit() {
    this.refreshData();
  }

  refreshData(): void {
    this.webapiService.getPeerGroupList().subscribe(data => {
      this.peerGroups = data;
      // Preserve the default sort (by name, ascending) on first load,
      // matching the original sortField="name" behaviour.
      this.sortData(this.currentSort);
      this.cdr.markForCheck();
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

  sortData(sort: Sort): void {
    this.currentSort = sort;
    if (!sort.active || sort.direction === '') {
      return;
    }
    const sorted = [...this.peerGroups].sort((a, b) => {
      const aValue = String((a as any)[sort.active] ?? '');
      const bValue = String((b as any)[sort.active] ?? '');
      const cmp = aValue.localeCompare(bValue);
      return sort.direction === 'asc' ? cmp : -cmp;
    });
    this.peerGroups = sorted;
  }
}
