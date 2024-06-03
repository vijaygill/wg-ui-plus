import { Component, OnInit } from '@angular/core';
import { WebapiService } from '../webapi.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { LicenseInfo } from '../webapi.entities';


@Component({
  selector: 'app-about',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule],
  templateUrl: './about.component.html',
  styleUrl: './about.component.scss'
})
export class AboutComponent implements OnInit {
  license: LicenseInfo = { license: '' } as LicenseInfo;
  constructor(private webapiService: WebapiService) {
  }

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.webapiService.getLicense().subscribe(data => {
      this.license = data;
    });
  }
}
