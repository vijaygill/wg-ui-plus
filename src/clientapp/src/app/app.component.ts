import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { RouterModule } from '@angular/router';
import { RouterOutlet } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { SidepanelComponent } from './sidepanel/sidepanel.component';
import { AppSharedModule } from './app-shared.module';
import { PrimeNGConfig } from 'primeng/api';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterModule, RouterOutlet, FormsModule, SidepanelComponent, AppSharedModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'wg-ui-plus';

  constructor(private primengConfig: PrimeNGConfig) { }

  ngOnInit() {
    // this.primengConfig.zIndex = {
    //   modal: 1100,    // dialog, sidebar
    //   overlay: 1000,  // dropdown, overlaypanel
    //   menu: 1000,     // overlay menus
    //   tooltip: 1100   // tooltip
    // };
  }
}
