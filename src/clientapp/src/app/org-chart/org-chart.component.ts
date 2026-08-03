import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { OrgChartNode } from '../webapi.entities';

interface OrgChartCell {
    node: OrgChartNode;
    depth: number;
    col: number;
    colspan: number;
}

interface OrgChartConnector {
    col: number;
    colspan: number;
    row: number;
}

@Component({
    standalone: true,
    selector: 'app-org-chart',
    imports: [CommonModule, MatIconModule, MatTooltipModule],
    templateUrl: './org-chart.component.html',
    styleUrl: './org-chart.component.scss'
})
export class OrgChartComponent implements OnChanges {

    @Input() value: OrgChartNode[] = [];

    cells: OrgChartCell[] = [];
    connectors: OrgChartConnector[] = [];
    gridColumnsStyle: string = 'none';
    gridRowsStyle: string = 'auto';

    ngOnChanges(): void {
        this.buildChart();
    }

    private buildChart(): void {
        this.cells = [];
        this.connectors = [];
        const nodes = this.value ?? [];
        if (nodes.length === 0) {
            this.gridColumnsStyle = 'none';
            this.gridRowsStyle = 'auto';
            return;
        }

        const spanOf = new Map<OrgChartNode, number>();
        let maxDepth = 0;

        const computeSpan = (node: OrgChartNode, depth: number): number => {
            const children = node.children ?? [];
            let span: number;
            if (children.length === 0) {
                span = 1;
            } else {
                span = children.reduce((sum, child) => sum + computeSpan(child, depth + 1), 0);
            }
            spanOf.set(node, span);
            return span;
        };

        const assignColumns = (node: OrgChartNode, depth: number, col: number): void => {
            maxDepth = Math.max(maxDepth, depth);
            const colspan = spanOf.get(node) ?? 1;
            this.cells.push({ node, depth, col, colspan });
            if ((node.children ?? []).length > 0) {
                this.connectors.push({ col, colspan, row: 2 * depth + 2 });
            }
            let nextCol = col;
            for (const child of node.children ?? []) {
                assignColumns(child, depth + 1, nextCol);
                nextCol += spanOf.get(child) ?? 1;
            }
        };

        let totalCols = 0;
        for (const root of nodes) {
            totalCols += computeSpan(root, 0);
        }
        let col = 0;
        for (const root of nodes) {
            assignColumns(root, 0, col);
            col += spanOf.get(root) ?? 1;
        }

        this.gridColumnsStyle = totalCols > 0 ? `repeat(${totalCols}, minmax(min-content, 1fr))` : 'none';
        this.gridRowsStyle = `repeat(${2 * maxDepth + 1}, auto)`;
    }

    cellGridColumn(cell: OrgChartCell): string {
        return `${cell.col + 1} / span ${cell.colspan}`;
    }

    cellGridRow(cell: OrgChartCell): string {
        return `${2 * cell.depth + 1}`;
    }

    connectorGridColumn(conn: OrgChartConnector): string {
        return `${conn.col + 1} / span ${conn.colspan}`;
    }

    connectorGridRow(conn: OrgChartConnector): string {
        return `${conn.row}`;
    }

    nodeIcon(node: OrgChartNode): string {
        switch (node.type) {
            case 'target': return 'track_changes';
            case 'peerGroup': return 'account_tree';
            case 'peer': return 'desktop_windows';
            default: return 'vpn_lock';  // root "VPN" node
        }
    }

    isRoot(node: OrgChartNode): boolean {
        return !node.type;
    }

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
