import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

import { WebapiService, Peer } from '../webapi.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [ CommonModule ],
  templateUrl: `./home.component.html`,
  styleUrl: './home.component.scss'
})
export class HomeComponent {
    peers: Peer[] = [];

    constructor( private webapiService: WebapiService) {}

    ngOnInit() {
        this.webapiService.getPeers().subscribe(peers => {
            this.peers = peers;
        });
    }
}
