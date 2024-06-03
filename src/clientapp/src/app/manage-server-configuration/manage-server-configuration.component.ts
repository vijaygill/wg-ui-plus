import { Component } from '@angular/core';
import { MessageService } from 'primeng/api';
import { ServerConfiguration, ServerValidationError, WebapiService, WireguardConfiguration } from '../webapi.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../app-shared.module';
import { ValidationErrorsDisplayComponent } from '../validation-errors-display/validation-errors-display.component';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthorizedViewComponent } from '../authorized-view/authorized-view.component';

@Component({
  selector: 'app-manage-server-configuration',
  standalone: true,
  imports: [CommonModule, FormsModule, AppSharedModule, ValidationErrorsDisplayComponent, AuthorizedViewComponent],
  providers: [MessageService],
  templateUrl: './manage-server-configuration.component.html',
  styleUrl: './manage-server-configuration.component.scss'
})
export class ManageServerConfigurationComponent {

  editItem: ServerConfiguration = {} as ServerConfiguration;

  validationResult!: ServerValidationError;

  constructor(private messageService: MessageService, private webapiService: WebapiService) { }

  ngOnInit() {
    this.refreshData();
  }

  refreshData(): void {
    // get the server configurations and use only first
    this.webapiService.getServerConfigurationList().subscribe(data => {
      this.editItem = data[0];
    });
  }

  ok() {
    this.webapiService.saveServerConfiguration(this.editItem)
      .subscribe({
        next: data => {
          this.messageService.add({ severity: 'success', summary: 'Success', detail: 'Server configuration saved.' });
          this.validationResult = { type: '', errors: [] } as ServerValidationError;
        },
        error: error => {
          let response = error as HttpErrorResponse;
          if (response) {
            this.validationResult = response.error as ServerValidationError;
          }
        },
        complete: () => {
        },
      });
  }


  cancel() {
    this.refreshData();
    this.messageService.add({ severity: 'warn ', summary: 'Cancel', detail: 'Server configuration reloaded from database.' });
  }

  wireguardConfiguration: WireguardConfiguration = {} as WireguardConfiguration;

  generateWireguardConfig() {
    this.webapiService.generateConfigurationFiles().subscribe(data => {
      this.messageService.add({ severity: 'success ', summary: 'Success', detail: 'Configuration files generated on server.' });
    });
  }

  restartWireguard() {
    this.webapiService.wireguardRestart().subscribe(data => {
      this.messageService.add({ severity: 'success ', summary: 'Success', detail: 'Wireguard restarted on server.' });
    });
  }

}
