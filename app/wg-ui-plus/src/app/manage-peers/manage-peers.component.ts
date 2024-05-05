import { Component } from '@angular/core';
import { Peer, WebapiService } from '../webapi.service';
import { MessageService } from 'primeng/api';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { PrimeNGModule } from '../primeng.module';

@Component({
  selector: 'app-manage-peers',
  standalone: true,
  imports: [CommonModule, FormsModule, PrimeNGModule],
  providers: [MessageService],
  templateUrl: './manage-peers.component.html',
  styleUrl: './manage-peers.component.scss'
})
export class ManagePeersComponent {

  peers: Peer[] = [];

  constructor(private messageService: MessageService, private webapiService: WebapiService) { }

  ngOnInit() {
    this.refreshData();
  }

  refreshData() {
    this.webapiService.getPeerList().subscribe(data => {
      this.peers = data;
    });
  }

}
