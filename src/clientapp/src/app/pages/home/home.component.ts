import { Component, OnInit, ChangeDetectionStrategy } from '@angular/core';

import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';

import { AppSharedModule } from '../../app-shared.module';

@Component({
    standalone: true,
    selector: 'app-home',
    imports: [FormsModule, RouterModule, AppSharedModule],
    templateUrl: `./home.component.html`,
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './home.component.scss'
})
export class HomeComponent implements OnInit {

  constructor() {
  }

  ngOnInit(): void {
  }

}
