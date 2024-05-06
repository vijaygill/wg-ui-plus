import { Component, EventEmitter, Input, Output } from '@angular/core';
import { PeerGroup, WebapiService } from '../webapi.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MessageService } from 'primeng/api';
import { PrimeNGModule } from '../primeng.module';

@Component({
  selector: 'app-manage-peer-groups-editor',
  standalone: true,
  imports: [CommonModule, FormsModule, PrimeNGModule],
  providers: [MessageService],
  templateUrl: './manage-peer-groups-editor.component.html',
  styleUrl: './manage-peer-groups-editor.component.scss'
})
export class ManagePeerGroupsEditorComponent {
  @Input()
  get editItem(): PeerGroup { return this.peerGroup; }
  set editItem(value: PeerGroup) { this.peerGroup = value; }

  peerGroup: PeerGroup = {} as PeerGroup;

  @Output() onFinish = new EventEmitter<boolean>();

  constructor(private messageService: MessageService, private webapiService: WebapiService) { }

  ngOnInit() {
  }

  ok() {
    this.webapiService.savePeerGroup(this.peerGroup).subscribe(data => {
      this.onFinish.emit(true);
    });
  }

  cancel() {
    debugger;
    this.onFinish.emit(false);
  }
}
