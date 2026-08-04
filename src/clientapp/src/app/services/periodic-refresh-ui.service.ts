import { Injectable } from '@angular/core';
import { Observable, Subject, interval } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class PeriodicRefreshUiService {

  onTimer: Subject<number> = new Subject<number>();
  private delay: number = 10000;
  private refresh_timer_subscription = interval(this.delay).subscribe(
    () => {
      this.performRefresh();
    }
  );

  constructor() { }

  performRefresh(): void {
    this.onTimer.next(this.delay / 1000);
  }

}

