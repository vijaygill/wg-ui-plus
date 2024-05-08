import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DockerContainer, Peer, WebapiService } from '../webapi.service';
import { MessageService } from 'primeng/api';
import { SharedModule } from '../shared.module';

@Component({
    selector: 'app-testpage',
    standalone: true,
    imports: [CommonModule, FormsModule, SharedModule],
    providers: [MessageService],
    templateUrl: './testpage.component.html',
    styleUrl: './testpage.component.scss'
})
export class TestpageComponent {
    peers: Peer[] = [];
    dockerContainers: DockerContainer[] = [];

    selectedPeers: number[] = [];

    constructor(private messageService: MessageService, private webapiService: WebapiService) { }

    ngOnInit() {
        this.refreshData();
        this.refreshDockerContainers();
    }

    refreshData() {
        this.webapiService.getPeerList().subscribe(data => {
            this.peers = data;
        });

    }

    refreshDockerContainers() {
        this.webapiService.getDockerContainerList().subscribe(data => {
            this.dockerContainers = data;
        });
    }

    startDockerContainer(name: string) {
        this.webapiService.startDockerContainer(name).subscribe(data => {
            this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Docker container started: ' + name });
            this.refreshDockerContainers();
        });
    }

    stopDockerContainer(name: string) {
        this.webapiService.stopDockerContainer(name).subscribe(data => {
            this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Docker container stopped: ' + name });
            this.refreshDockerContainers();
        });
    }
}
