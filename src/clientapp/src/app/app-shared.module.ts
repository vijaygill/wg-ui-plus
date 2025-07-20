import { NgModule } from '@angular/core';

//import { AccordionModule } from 'primeng/accordion';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { CascadeSelectModule } from 'primeng/cascadeselect';
import { CheckboxModule } from 'primeng/checkbox';
import { ConfirmDialog, ConfirmDialogModule } from 'primeng/confirmdialog';
//import { ConfirmPopupModule } from 'primeng/confirmpopup';
//import { ContextMenuModule } from 'primeng/contextmenu';
import { DataViewModule } from 'primeng/dataview';
import { DialogModule } from 'primeng/dialog';
import { DividerModule } from 'primeng/divider';
import { DragDropModule } from 'primeng/dragdrop';
//import { DockModule } from 'primeng/dock';
//import { DynamicDialogModule } from 'primeng/dynamicdialog';
import { ImageModule } from 'primeng/image';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
//import { KnobModule } from 'primeng/knob';
import { ListboxModule } from 'primeng/listbox';
//import { MegaMenuModule } from 'primeng/megamenu';
import { MenuModule } from 'primeng/menu';
//import { MenubarModule } from 'primeng/menubar';
import { MessageModule } from 'primeng/message';
//import { MeterGroupModule } from 'primeng/metergroup';
//import { MultiSelectModule } from 'primeng/multiselect';
//import { OrderListModule } from 'primeng/orderlist';
import { OrganizationChartModule } from 'primeng/organizationchart';
//import { PaginatorModule } from 'primeng/paginator';
//import { PanelMenuModule } from 'primeng/panelmenu';
import { PanelModule } from 'primeng/panel';
import { PasswordModule } from 'primeng/password';
import { PickListModule } from 'primeng/picklist';
//import { ProgressBarModule } from 'primeng/progressbar';
//import { ProgressSpinnerModule } from 'primeng/progressspinner';
//import { RadioButtonModule } from 'primeng/radiobutton';
//import { ScrollPanelModule } from 'primeng/scrollpanel';
//import { ScrollerModule } from 'primeng/scroller';
//import { SelectButtonModule } from 'primeng/selectbutton';
//import { SidebarModule } from 'primeng/sidebar';
//import { SliderModule } from 'primeng/slider';
//import { SpeedDialModule } from 'primeng/speeddial';
//import { SplitButtonModule } from 'primeng/splitbutton';
//import { StepperModule } from 'primeng/stepper';
//import { StepsModule } from 'primeng/steps';
import { TabsModule } from 'primeng/tabs';
import { TableModule } from 'primeng/table';
//import { TieredMenuModule } from 'primeng/tieredmenu';
//import { TimelineModule } from 'primeng/timeline';
import { ToastModule } from 'primeng/toast';
//import { ToggleButtonModule } from 'primeng/togglebutton';
//import { ToolbarModule } from 'primeng/toolbar';
import { TooltipModule } from 'primeng/tooltip';
//import { TreeModule } from 'primeng/tree';
//import { TreeSelectModule } from 'primeng/treeselect';
//import { TreeTableModule } from 'primeng/treetable';
//import { TriStateCheckboxModule } from 'primeng/tristatecheckbox';
import { ValidationErrorsDisplayComponent } from './validation-errors-display/validation-errors-display.component';
import { AutoFocusModule } from 'primeng/autofocus';
import { ConfirmationService, MessageService } from 'primeng/api';

let modules = [
    AutoFocusModule,
    ButtonModule, CardModule, 
    CascadeSelectModule,
    CheckboxModule,
    ConfirmDialog, ConfirmDialogModule,
    DataViewModule, DialogModule, DividerModule,
    DragDropModule,
    ImageModule,
    InputNumberModule, InputTextModule,
    ListboxModule,
    MenuModule,
    MessageModule,
    OrganizationChartModule,
    PanelModule,
    PasswordModule,
    PickListModule,
    TableModule, 
    TabsModule,
    ToastModule,
    TooltipModule,
    ValidationErrorsDisplayComponent,
];

@NgModule({
    imports: modules,
    exports: modules,
    providers: [ConfirmationService, MessageService]
})
export class AppSharedModule {
}
