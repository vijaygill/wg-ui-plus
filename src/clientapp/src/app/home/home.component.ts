import { Component, OnInit } from '@angular/core';

import { FormsModule } from '@angular/forms';

import { AppSharedModule } from '../app-shared.module';
import { MessageService } from 'primeng/api';

@Component({
    standalone: true,
    selector: 'app-home',
    imports: [FormsModule, AppSharedModule],
    providers: [MessageService],
    templateUrl: `./home.component.html`,
    styleUrl: './home.component.scss'
})
export class HomeComponent implements OnInit {

  constructor() {
  }

  ngOnInit(): void {
  }

  ngOnDestroy() {
  }

}
