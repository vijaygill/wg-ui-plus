import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { PrimeNGModule } from '../primeng.module';
import { MessageService } from 'primeng/api';

import { WebapiService } from '../webapi.service';
import { Peer, IpTablesChain, DockerContainer } from '../webapi.service';


@Component({
  selector: 'app-home',
  standalone: true,
  imports: [ CommonModule, FormsModule, PrimeNGModule ],
  providers: [ MessageService ],
  templateUrl: `./home.component.html`,
  styleUrl: './home.component.scss'
})
export class HomeComponent {
    peers: Peer[] = [];
    ipTablesChains: IpTablesChain[] = [];
    dockerContainers: DockerContainer[] = [];

    selectedPeers : number[] = [];

    constructor(private messageService: MessageService, private webapiService: WebapiService) {}

    ngOnInit() {
        this.refreshData();
        this.refreshDockerContainers();
    }

    refreshData(){
        this.webapiService.getPeerList().subscribe(data => {
            this.peers = data;
        });

        this.webapiService.getIpTablesChainList().subscribe(data => {
            this.ipTablesChains = data;
        });
    }

    refreshDockerContainers(){
        this.webapiService.getDockerContainerList().subscribe(data => {
            this.dockerContainers = data;
        });
    }

    startDockerContainer(name: string){
        this.webapiService.startDockerContainer(name).subscribe(data => {
            this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Docker container started: ' + name });
            this.refreshDockerContainers();
        });
    }
    
    stopDockerContainer(name: string){
        this.webapiService.stopDockerContainer(name).subscribe(data => {
            this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Docker container stopped: ' + name });
            this.refreshDockerContainers();
        });
    }
}
