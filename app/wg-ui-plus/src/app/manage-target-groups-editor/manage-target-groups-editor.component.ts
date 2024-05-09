import { Component, EventEmitter, Input, Output } from '@angular/core';
import { TargetGroup, WebapiService } from '../webapi.service';
import { Message, MessageService } from 'primeng/api';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';

@Component({
  selector: 'app-manage-target-groups-editor',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule],
  templateUrl: './manage-target-groups-editor.component.html',
  styleUrl: './manage-target-groups-editor.component.scss'
})
export class ManageTargetGroupsEditorComponent {
  @Input()
  get editItem(): TargetGroup { return this.targetGroup; }
  set editItem(value: TargetGroup) {
    this.targetGroup = value;
    this.webapiService.getTargetGroup(value.id).subscribe(data => {
      this.targetGroup = data;
    });
  }

  targetGroup: TargetGroup = {} as TargetGroup;

  @Output() onFinish = new EventEmitter<boolean>();

  messages: Message[] = [
    { severity: 'info', detail: 'In-built Target-Groups are read-only.' }
  ];

  constructor(private messageService: MessageService, private webapiService: WebapiService) { }

  ok() {
    this.webapiService.saveTargetGroup(this.targetGroup).subscribe(data => {
      this.onFinish.emit(true);
    });
  }

  cancel() {
    this.onFinish.emit(false);
  }

}
