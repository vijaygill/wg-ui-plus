import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { OrgChartNode } from '../webapi.entities';

@Component({
    standalone: true,
    selector: 'app-org-chart',
    imports: [CommonModule, MatIconModule, MatTooltipModule],
    templateUrl: './org-chart.component.html',
    styleUrl: './org-chart.component.scss'
})
export class OrgChartComponent {

    @Input() value: OrgChartNode[] = [];

    disabledTooltip(node: OrgChartNode): string {
        switch (node.type) {
            case 'target':
                return 'Target disabled. Access to this Target is disabled for everyone.';
            case 'peerGroup':
                return "Peer-Group disabled. All Peers in this Peer-Group won't have access to the linked Target.";
            case 'peer':
                return "Peer disabled. This Peer won't have access to the Target to the linked Peer-Group.";
            default:
                return 'Disabled';
        }
    }
}
