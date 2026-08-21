import { Component, OnInit, ChangeDetectionStrategy, signal } from '@angular/core';
import { WebapiService } from '../../services/webapi.service';

import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../../app-shared.module';
import { LicenseInfo } from '../../webapi.entities';


@Component({
    standalone: true,
    selector: 'app-about',
    imports: [FormsModule, AppSharedModule],
    templateUrl: './app-about.component.html',
    changeDetection: ChangeDetectionStrategy.Eager,
    styleUrl: './app-about.component.scss'
})
export class AboutComponent implements OnInit {
  license = signal<LicenseInfo>({ license: '' } as LicenseInfo);
  constructor(private webapiService: WebapiService) {
  }

  ngOnInit(): void {
    this.loadData();
  }

  loadData(): void {
    this.webapiService.getLicense().subscribe(data => {
      this.license.set(data);
    });
  }
}
