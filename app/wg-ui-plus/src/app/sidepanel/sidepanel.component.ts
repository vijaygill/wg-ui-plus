import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule, RouterOutlet } from '@angular/router';
import { MenuItem, SharedModule } from 'primeng/api';
import { MenuModule } from 'primeng/menu';


@Component({
  selector: 'app-sidepanel',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, RouterOutlet, SharedModule, MenuModule],
  templateUrl: './sidepanel.component.html',
  styleUrl: './sidepanel.component.scss'
})
export class SidepanelComponent {
  items: MenuItem[] = [
    {
      label: 'Navigate',
      items: [
        {
          label: 'Home',
          route: '/home',
        },
        {
          label: 'Peer-Groups',
          route: '/manage-peer-groups',
        },
        {
          label: 'Peers',
          route: '/manage-peers',
        },
        {
          label: 'Target-Groups',
          route: '/manage-target-groups',
        },
        {
          label: 'Targets',
          route: '/manage-targets',
        },
        {
          label: 'Test',
          route: '/test-page',
        },
        {
          label: 'About',
          route: '/about',
        },
      ]
    }
  ];

  constructor(private router: Router) { }
}
