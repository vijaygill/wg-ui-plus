import { Component } from '@angular/core';
import { MessageService } from 'primeng/api';
import { ServerConfiguration, WebapiService } from '../webapi.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SharedModule } from '../shared.module';

@Component({
  selector: 'app-manage-server-configuration',
  standalone: true,
  imports: [CommonModule, FormsModule, SharedModule],
  providers: [MessageService],
  templateUrl: './manage-server-configuration.component.html',
  styleUrl: './manage-server-configuration.component.scss'
})
export class ManageServerConfigurationComponent {

  editItem: ServerConfiguration = {} as ServerConfiguration;

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
    this.webapiService.saveServerConfiguration(this.editItem).subscribe(data => {

    });
  }

  cancel() {
    this.refreshData();
  }

}
