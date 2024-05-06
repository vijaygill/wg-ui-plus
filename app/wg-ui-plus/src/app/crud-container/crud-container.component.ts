import { Component, ContentChild, ElementRef, EventEmitter, Input, Output, TemplateRef } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-crud-container',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './crud-container.component.html',
  styleUrl: './crud-container.component.scss'
})
export class CrudContainerComponent<T> {
  isEditing: boolean = false;

  item: T = {} as T;

  @ContentChild("list") listControl!: TemplateRef<any>;
  @ContentChild("editor") editorControl!: TemplateRef<any>;

  ngOnInit() {
  }

  listControlContext = {
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
