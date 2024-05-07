import { Component, ContentChild, ElementRef, EventEmitter, Input, Output, TemplateRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PrimeNGModule } from '../primeng.module';

@Component({
  selector: 'app-crud-container',
  standalone: true,
  imports: [CommonModule, PrimeNGModule],
  templateUrl: './crud-container.component.html',
  styleUrl: './crud-container.component.scss'
})
export class CrudContainerComponent<T> {
  @Input() title: string = '<No Title>';
  isEditing: boolean = false;
  item: T = {} as T;

  @ContentChild("list") listControl!: TemplateRef<any>;
  @ContentChild("editor") editorControl!: TemplateRef<any>;

  ngOnInit() {
  }

  listControlContext = {
    onNewItem: (item: T) =>{
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
