import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { MessageService } from 'primeng/api';
import { Target, WebapiService } from '../webapi.service';

@Component({
  selector: 'app-manage-targets-list',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule],
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
      let peer = {} as Target;
      this.onNewItem.emit(peer);
    }
  }

  editItem(peer: Target): void {
    if (this.onEdit) {
      this.onEdit.emit(peer);
    }
  }
}
