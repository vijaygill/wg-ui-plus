import { Component, ContentChild, Input, TemplateRef, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppSharedModule } from '../app-shared.module';
import { Router } from '@angular/router';
import { AuthorizedViewComponent } from '../authorized-view/authorized-view.component';
import { LoginService } from '../login-service';
import { EditStateService } from '../edit-state.service';
import { Subscription } from 'rxjs';

@Component({
    standalone: true,
    selector: 'app-crud-container',
    imports: [CommonModule, AppSharedModule, AuthorizedViewComponent],
    templateUrl: './crud-container.component.html',
    styleUrl: './crud-container.component.scss'
})
export class CrudContainerComponent<T> implements OnDestroy {
  @Input() header!: string;
  @Input() subheader!: string;
  isEditing: boolean = false;
  item: T = {} as T;

  @ContentChild("list") listControl!: TemplateRef<any>;
  @ContentChild("editor") editorControl!: TemplateRef<any>;

  private editStateSubscription!: Subscription;

  constructor(private router: Router, private loginService: LoginService, private editStateService: EditStateService) {
    this.editStateSubscription = this.editStateService.isEditing$.subscribe(editing => {
      // Sync with service state if needed
    });
  }

  ngOnDestroy(): void {
    if (this.editStateSubscription) {
      this.editStateSubscription.unsubscribe();
    }
  }

  listControlContext = {
    onNewItem: (item: T) => {
      this.item = item;
      this.isEditing = true;
      this.editStateService.setEditing(true);
    },
    onEdit: (item: T) => {
      this.item = item;
      this.isEditing = true;
      this.editStateService.setEditing(true);
    }
  };

  editControlContext = {
    getEditItem: () => { return this.item; },
    onFinish: (item: T) => {
      this.isEditing = false;
      this.editStateService.setEditing(false);
    }
  };
}
