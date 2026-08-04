import { Component, ContentChild, Input, TemplateRef, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppSharedModule } from '../../app-shared.module';
import { Router } from '@angular/router';
import { AuthorizedViewComponent } from '../authorized-view/authorized-view.component';
import { LoginService } from '../../services/login.service';

@Component({
    standalone: true,
    selector: 'app-crud-container',
    imports: [CommonModule, AppSharedModule, AuthorizedViewComponent],
    templateUrl: './crud-container.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './crud-container.component.scss'
})
export class CrudContainerComponent<T> {
  @Input() header!: string;
  @Input() subheader!: string;
  isEditing: boolean = false;
  item: T = {} as T;

  @ContentChild("list") listControl!: TemplateRef<any>;
  @ContentChild("editor") editorControl!: TemplateRef<any>;

  constructor(private router: Router, private loginService: LoginService) { }

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
    getEditItem: () => { return this.item; },
    onFinish: (item: T) => {
      this.isEditing = false;
    }
  };
}
