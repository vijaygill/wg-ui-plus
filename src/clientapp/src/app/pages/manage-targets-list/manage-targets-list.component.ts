
import { Component, EventEmitter, Output, ChangeDetectionStrategy, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../../app-shared.module';
import { Sort } from '@angular/material/sort';
import { PeerGroup, Target } from '../../webapi.entities';
import { WebapiService } from '../../services/webapi.service';

@Component({
    standalone: true,
    selector: 'app-manage-targets-list',
    imports: [FormsModule, AppSharedModule],
    templateUrl: './manage-targets-list.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './manage-targets-list.component.scss'
})
export class ManageTargetsListComponent {
  targets = signal<Target[]>([]);
  private currentSort: Sort = { active: 'name', direction: 'asc' };

  constructor(private webapiService: WebapiService) { }

  ngOnInit() {
    this.refreshData();
  }

  refreshData(): void {
    this.webapiService.getTargetList().subscribe(data => {
      this.targets.set(data);
      // Preserve the default sort (by name, ascending) on first load,
      // matching the original sortField="name" behaviour.
      this.sortData(this.currentSort);
    });
  }

  @Output() onNewItem = new EventEmitter<Target>();
  @Output() onEdit = new EventEmitter<Target>();

  newItem(): void {
    if (this.onNewItem) {
      let target = {
        allow_modify_self: true,
        allow_modify_peer_groups: true,
        peer_group_ids: [] as number[],
        peer_groups: [] as PeerGroup[],
      } as Target;
      this.onNewItem.emit(target);
    }
  }

  editItem(peer: Target): void {
    if (this.onEdit) {
      this.onEdit.emit(peer);
    }
  }

  sortData(sort: Sort): void {
    this.currentSort = sort;
    if (!sort.active || sort.direction === '') {
      return;
    }
    const sorted = [...this.targets()].sort((a, b) => {
      const aValue = String((a as any)[sort.active] ?? '');
      const bValue = String((b as any)[sort.active] ?? '');
      const cmp = aValue.localeCompare(bValue);
      return sort.direction === 'asc' ? cmp : -cmp;
    });
    this.targets.set(sorted);
  }
}
