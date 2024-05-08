import { Component, EventEmitter, Input, Output } from '@angular/core';
import { Target, WebapiService } from '../webapi.service';
import { MessageService } from 'primeng/api';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SharedModule } from '../shared.module';

@Component({
  selector: 'app-manage-targets-editor',
  standalone: true,
  imports: [CommonModule, FormsModule, SharedModule],
  templateUrl: './manage-targets-editor.component.html',
  styleUrl: './manage-targets-editor.component.scss'
})
export class ManageTargetsEditorComponent {
  @Input()
  get editItem(): Target { return this.target; }
  set editItem(value: Target) {
    this.target = value;
    this.webapiService.getTarget(value.id).subscribe(data => {
      this.target = data;
    });
  }

  target: Target = {} as Target;

  @Output() onFinish = new EventEmitter<boolean>();

  constructor(private messageService: MessageService, private webapiService: WebapiService) { }

  ok() {
    this.webapiService.saveTarget(this.target).subscribe(data => {
      this.onFinish.emit(true);
    });
  }

  cancel() {
    this.onFinish.emit(false);
  }

}