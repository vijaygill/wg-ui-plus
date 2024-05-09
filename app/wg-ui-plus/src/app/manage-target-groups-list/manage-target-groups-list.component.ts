import { Component, EventEmitter, Output } from '@angular/core';
import { TargetGroup, WebapiService } from '../webapi.service';
import { MessageService } from 'primeng/api';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';

@Component({
  selector: 'app-manage-target-groups-list',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule],
  providers: [MessageService],
  templateUrl: './manage-target-groups-list.component.html',
  styleUrl: './manage-target-groups-list.component.scss'
})
export class ManageTargetGroupsListComponent {
  targetGroups: TargetGroup[] = [];

  constructor(private messageService: MessageService, private webapiService: WebapiService) { }

  ngOnInit() {
    this.refreshData();
  }

  refreshData(): void {
    this.webapiService.getTargetGroupList().subscribe(data => {
      this.targetGroups = data;
    });
  }

  @Output() onNewItem = new EventEmitter<TargetGroup>();
  @Output() onEdit = new EventEmitter<TargetGroup>();

  newItem(): void {
    if (this.onNewItem) {
      let peer = {} as TargetGroup;
      this.onNewItem.emit(peer);
    }
  }

  editItem(peer: TargetGroup): void {
    if (this.onEdit) {
      this.onEdit.emit(peer);
    }
  }
}
