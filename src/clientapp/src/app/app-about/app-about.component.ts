import { ChangeDetectionStrategy, Component, OnInit } from '@angular/core';
import { WebapiService } from '../webapi.service';

import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { LicenseInfo } from '../webapi.entities';


@Component({
    standalone: true,
    changeDetection: ChangeDetectionStrategy.OnPush,
    selector: 'app-about',
    imports: [FormsModule, AppSharedModule],
    templateUrl: './app-about.component.html',
    styleUrl: './app-about.component.scss'
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
