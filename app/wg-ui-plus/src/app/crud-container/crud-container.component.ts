import { Component, ContentChild, ElementRef, EventEmitter, Input, Output, TemplateRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SharedModule } from '../shared.module';

@Component({
  selector: 'app-crud-container',
  standalone: true,
  imports: [CommonModule, SharedModule],
  templateUrl: './crud-container.component.html',
  styleUrl: './crud-container.component.scss'
})
export class CrudContainerComponent<T> {
  @Input() header: string = '<No Header>';
  @Input() subheader!: string;
  isEditing: boolean = false;
  item: T = {} as T;

  @ContentChild("list") listControl!: TemplateRef<any>;
  @ContentChild("editor") editorControl!: TemplateRef<any>;

  ngOnInit() {
  }

  listControlContext = {
    onNewItem: (item: T) => {
      this.item = item;
      this.isEditing = true;
    },
    onEdit: (item: T) => {
      this.item = item;
      this.isEditing = true;
    }
  };

  editControlContext = {
    item: () => { return this.item; },
    onFinish: (item: T) => {
      this.isEditing = false;
    }
  };
}
