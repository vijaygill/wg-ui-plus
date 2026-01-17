
import { ChangeDetectionStrategy, Component, EventEmitter, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { MessageService } from 'primeng/api';
import { PeerGroup, Target } from '../webapi.entities';
import { WebapiService } from '../webapi.service';

@Component({
    standalone: true,
    changeDetection: ChangeDetectionStrategy.OnPush,
    selector: 'app-manage-targets-list',
    imports: [FormsModule, AppSharedModule],
    providers: [MessageService],
    templateUrl: './manage-targets-list.component.html',
    styleUrl: './manage-targets-list.component.scss'
})
export class ManageTargetsListComponent {
  targets: Target[] = [];

  constructor(private messageService: MessageService, private webapiService: WebapiService) { }

  ngOnInit() {
    this.refreshData();
  }

  refreshData(): void {
    this.webapiService.getTargetList().subscribe(data => {
      this.targets = data;
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
}
