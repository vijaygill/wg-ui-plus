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
    blah: string = '';

    constructor( private webapiService: WebapiService) {}

    ngOnInit() {
        this.refreshData();
    }

    refreshData(){
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

    startDockerContainer(name: string){
        this.webapiService.startDockerContainer(name).subscribe(data => {
            this.refreshData();
        });
    }
    
    stopDockerContainer(name: string){
        this.webapiService.stopDockerContainer(name).subscribe(data => {
            this.refreshData();
        });
    }
}
