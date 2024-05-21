import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { AppSharedModule } from '../app-shared.module';
import { MessageService, TreeNode } from 'primeng/api';
import { WebapiService } from '../webapi.service';
import { Init } from 'v8';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule],
  providers: [MessageService],
  templateUrl: `./home.component.html`,
  styleUrl: './home.component.scss'
})
export class HomeComponent implements OnInit {

  items!: TreeNode[];

  constructor(private webapiService: WebapiService) {
  }

  ngOnInit(): void {
    this.loadData();
  }

  loadData() {
    this.webapiService.getTargetHeirarchy().subscribe(data => {
      this.items = data;
    }
    );
  }

}
