import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { PrimeNGModule } from '../primeng.module';

import { WebapiService } from '../webapi.service';
import { Peer, IpTablesChain, DockerContainer } from '../webapi.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [ CommonModule, FormsModule, PrimeNGModule ],
  templateUrl: `./home.component.html`,
  styleUrl: './home.component.scss'
})
export class HomeComponent {
    peers: Peer[] = [];
    ipTablesChains: IpTablesChain[] = [];
    dockerContainers: DockerContainer[] = [];

    selectedPeers : number[] = [];

    constructor( private webapiService: WebapiService) {}

    ngOnInit() {
        this.webapiService.getPeerList().subscribe(data => {
            this.peers = data;
        });

        this.webapiService.getIpTablesChainList().subscribe(data => {
            this.ipTablesChains = data;
        });
        this.webapiService.getDockerContainerList().subscribe(data => {
            this.dockerContainers = data;
        });
    }
}
