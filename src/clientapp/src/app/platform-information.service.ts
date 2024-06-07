import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import { PlatformInformation } from './webapi.entities';

@Injectable({
  providedIn: 'root'
})
export class PlatformInformationService {
  platformInformation: Subject<PlatformInformation> = new Subject<PlatformInformation>();

  constructor() {
    window.onresize = () => this.updatePlatformInformation();
    this.updatePlatformInformation();
  }

  checkPlatform(): void {
    this.updatePlatformInformation();
  }

  private updatePlatformInformation(): void {
    let info = {
      is_small_screen: this.isMobile() || window.innerWidth <= 900,
    } as PlatformInformation;
    this.platformInformation.next(info);
  }

  private isMobile(): boolean {
    const regex = /Mobi|Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i;
    return regex.test(navigator.userAgent);
  }


}
