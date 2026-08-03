import { Component, ContentChild, Input, TemplateRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CdkDragDrop, DragDropModule, transferArrayItem } from '@angular/cdk/drag-drop';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

export interface DualListItem {
    id?: number | string;
    name: string;
}

@Component({
    standalone: true,
    selector: 'app-dual-list',
    imports: [CommonModule, DragDropModule, MatIconModule, MatButtonModule, MatTooltipModule],
    templateUrl: './dual-list.component.html',
    styleUrl: './dual-list.component.scss'
})
export class DualListComponent<T extends DualListItem> {

    private _source: T[] = [];
    private _selected: T[] = [];

    @Input() set source(v: T[] | undefined) { this._source = v ?? []; }
    get source(): T[] { return this._source; }
    @Input() set selected(v: T[] | undefined) { this._selected = v ?? []; }
    get selected(): T[] { return this._selected; }
    @Input() sourceHeader: string = '';
    @Input() targetHeader: string = '';
    @Input() disabled: boolean = false;
    @Input() height: string = '14rem';

    @ContentChild('itemTemplate') itemTemplate!: TemplateRef<any>;

    private sourceSelection = new Set<T>();
    private targetSelection = new Set<T>();

    onDrop(event: CdkDragDrop<T[]>): void {
        if (this.disabled) {
            return;
        }
        if (!this.source || !this.selected) {
            return;
        }
        const previous = event.previousContainer.data;
        const current = event.container.data;
        if (previous === current) {
            // Fixed order: dragging within the same pane does nothing.
            return;
        }
        transferArrayItem(previous, current, event.previousIndex, event.currentIndex);
        this.sortBoth();
    }

    onItemClick(item: T, pane: 'source' | 'target', event: MouseEvent): void {
        if (this.disabled) {
            return;
        }
        const selection = this.selectionFor(pane);
        if (event.ctrlKey || event.metaKey) {
            if (selection.has(item)) {
                selection.delete(item);
            } else {
                selection.add(item);
            }
        } else {
            selection.clear();
            selection.add(item);
        }
    }

    isSelected(item: T, pane: 'source' | 'target'): boolean {
        return this.selectionFor(pane).has(item);
    }

    moveSelected(from: T[], to: T[]): void {
        if (this.disabled) {
            return;
        }
        if (!this.source || !this.selected) {
            return;
        }
        const selection = this.selectionFor(from === this.source ? 'source' : 'target');
        const items = Array.from(selection);
        selection.clear();
        items.forEach(item => {
            const index = from.indexOf(item);
            if (index >= 0) {
                from.splice(index, 1);
                to.push(item);
            }
        });
        this.sortBoth();
    }

    moveAll(from: T[], to: T[]): void {
        if (this.disabled) {
            return;
        }
        if (!this.source || !this.selected) {
            return;
        }
        this.selectionFor(from === this.source ? 'source' : 'target').clear();
        to.push(...from.splice(0, from.length));
        this.sortBoth();
    }

    trackByFn(index: number, item: T): number | string | T {
        return item.id !== undefined ? item.id : item;
    }

    private selectionFor(pane: 'source' | 'target'): Set<T> {
        return pane === 'source' ? this.sourceSelection : this.targetSelection;
    }

    private sortBoth(): void {
        this.sortByName(this.source ?? []);
        this.sortByName(this.selected ?? []);
    }

    private sortByName(items: T[]): void {
        items.sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()));
    }
}
