import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class EditStateService {
  private isEditingSubject = new BehaviorSubject<boolean>(false);
  isEditing$ = this.isEditingSubject.asObservable();

  setEditing(editing: boolean): void {
    this.isEditingSubject.next(editing);
  }

  isEditing(): boolean {
    return this.isEditingSubject.value;
  }
}
