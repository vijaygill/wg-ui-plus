import { Injectable, signal } from '@angular/core';
import { PlatformInformation } from '../webapi.entities';

@Injectable({
  providedIn: 'root'
})
export class PlatformInformationService {

  private platformInformationSignal = signal<PlatformInformation>({ is_small_screen: false });

  /** Current platform information; signal writes schedule change detection. */
  readonly platformInformation = this.platformInformationSignal.asReadonly();

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
    this.platformInformationSignal.set(info);
  }

  private isMobile(): boolean {
    const regex = /Mobi|Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i;
    return regex.test(navigator.userAgent);
  }


}
