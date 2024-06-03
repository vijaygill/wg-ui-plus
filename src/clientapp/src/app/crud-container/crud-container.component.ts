import { Component, ContentChild, ElementRef, EventEmitter, Input, Output, TemplateRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AppSharedModule } from '../app-shared.module';
import { LoginService } from '../login/login.component';
import { Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { UserSessionInfo } from '../webapi.service';

@Component({
  selector: 'app-crud-container',
  standalone: true,
  imports: [CommonModule, AppSharedModule],
  templateUrl: './crud-container.component.html',
  styleUrl: './crud-container.component.scss'
})
export class CrudContainerComponent<T> {
  @Input() header: string = '<No Header>';
  @Input() subheader!: string;
  isEditing: boolean = false;
  item: T = {} as T;

  useDialogForEditor: boolean = false;
  userSessionInfo!: UserSessionInfo;
  loginServiceSubscription !: Subscription;

  @ContentChild("list") listControl!: TemplateRef<any>;
  @ContentChild("editor") editorControl!: TemplateRef<any>;

  constructor(private router: Router, private loginService: LoginService) { }

  ngOnInit(): void {
    this.loginServiceSubscription = this.loginService.getUserSessionInfo().subscribe(data => {
      this.userSessionInfo = data;
      if (this.userSessionInfo.is_logged_in) {
        this.router.navigate(['/home']);
      }
      else {
        this.router.navigate(['/']);
      }
    });
    this.loginService.checkIsUserAuthenticated();
  }

  ngOnDestroy() {
    if (this.loginServiceSubscription) {
      this.loginServiceSubscription.unsubscribe();
    }
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
    getEditItem: () => { return this.item; },
    onFinish: (item: T) => {
      this.isEditing = false;
    }
  };
}
