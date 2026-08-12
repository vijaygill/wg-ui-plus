import { ChangeDetectionStrategy, Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { ChangeUserPasswordInfo, McpConfiguration, ServerConfiguration, ServerStatus, ServerValidationError, UserSessionInfo, WireguardConfiguration } from '../../webapi.entities';

import { FormsModule } from '@angular/forms';
import { AppSharedModule } from '../../app-shared.module';
import { ValidationErrorsDisplayComponent } from '../../controls/validation-errors-display/validation-errors-display.component';
import { HttpErrorResponse } from '@angular/common/http';
import { AuthorizedViewComponent } from '../../controls/authorized-view/authorized-view.component';
import { Subscription } from 'rxjs';
import { Router } from '@angular/router';
import { LoginService } from '../../services/login.service';
import { WebapiService } from '../../services/webapi.service';
import { NotificationService } from '../../services/notification.service';
import { ConfirmationDialogService } from '../../services/confirmation-dialog.service';

@Component({
  standalone: true,
  selector: 'app-manage-server-configuration',
  imports: [FormsModule, AppSharedModule, ValidationErrorsDisplayComponent, AuthorizedViewComponent],
  templateUrl: './manage-server-configuration.component.html',
  changeDetection: ChangeDetectionStrategy.Eager,
  styleUrl: './manage-server-configuration.component.scss'
})
export class ManageServerConfigurationComponent implements OnInit, OnDestroy {

  editItem: ServerConfiguration = {} as ServerConfiguration;
  validationResult!: ServerValidationError;

  /** Serialized snapshot of the editable fields as originally loaded. */
  private snapshot = '';

  changeUserPasswordInfo: ChangeUserPasswordInfo = {} as ChangeUserPasswordInfo;

  serverStatus !: ServerStatus;

  userSessionInfo!: UserSessionInfo;
  loginServiceSubscription !: Subscription;
  serverStatusSubscription !: Subscription;
  refreshDataSubscription !: Subscription;
  mcpConfigurationSubscription !: Subscription;
  mcpActionSubscription !: Subscription;
  testEmailSubscription !: Subscription;
  mcpConfirmationSubscription !: Subscription;
  saveConfigurationSubscription !: Subscription;
  changePasswordSubscription !: Subscription;
  mcpConfiguration: McpConfiguration = {} as McpConfiguration;
  mcpLoadError = '';
  mcpConfigurationLoading = true;
  mcpUpdating = false;
  mcpTokenVisible = false;
  revealedMcpToken: string | null = null;
  private savedMcpEnabled = false;
  private mcpTokenHideTimer: ReturnType<typeof setTimeout> | null = null;
  private mcpTokenFocusTimer: ReturnType<typeof setTimeout> | null = null;
  private destroyed = false;
  private readonly environmentVariableNames: { [field: string]: string } = {
    network_address: 'WG_NETWORK_ADDRESS',
    host_name_external: 'WG_HOST_NAME_EXTERNAL',
    local_networks: 'WG_LOCAL_NETWORKS',
    upstream_dns_ip_address: 'WG_UPSTREAM_DNS_SERVER',
    port_external: 'WG_PORT_EXTERNAL',
    port_internal: 'WG_PORT_INTERNAL',
     strict_allowed_ips_in_peer_config: 'WG_STRICT_ALLOWED_IPS_IN_PEER_CONFIG',
     allow_check_updates: 'WG_ALLOW_CHECK_UPDATES',
     mcp_server_enabled: 'WG_MCP_SERVER_ENABLED'
  };

  @ViewChild('mcpTokenInput') private mcpTokenInput?: ElementRef<HTMLInputElement>;


  constructor(private notification: NotificationService,
    private webapiService: WebapiService,
    private router: Router, private loginService: LoginService, private confirmation: ConfirmationDialogService) { }

  ngOnInit(): void {
    this.loginServiceSubscription = this.loginService.getUserSessionInfo().subscribe(data => {
      this.userSessionInfo = data;
      this.userSessionInfo.message = "";
      if (!this.userSessionInfo.is_logged_in) {
        this.router.navigate(['/login']);
      }
    });
    this.loginService.checkIsUserAuthenticated();
    this.serverStatusSubscription = this.webapiService.serverStatus.subscribe(data => {
      if (!this.serverStatus || (this.serverStatus && data && this.serverStatus.last_db_change_datetime < data.last_db_change_datetime)) {
        this.refreshData();
        this.serverStatus = data;
      }
    });
    this.refreshData();
    this.mcpConfigurationSubscription = this.webapiService.getMcpConfiguration().subscribe({
      next: data => {
        if (this.destroyed) {
          return;
        }
        this.mcpConfiguration = data;
        this.savedMcpEnabled = data.mcp_enabled;
        this.resetRevealedMcpToken();
        this.mcpConfigurationLoading = false;
        this.mcpLoadError = '';
      },
      error: () => {
        if (this.destroyed) {
          return;
        }
        // MCP may not be available while an older database is being migrated or
        // when the session expired. Keep the rest of this page usable.
        this.mcpLoadError = 'MCP configuration could not be loaded. Refresh after signing in again.';
        this.mcpConfigurationLoading = false;
        this.resetRevealedMcpToken();
        this.mcpConfiguration = {
          mcp_enabled: false,
          effective_enabled: false,
          environment_override: false,
          environment_enabled: null,
          mcp_token: null
        };
      }
    });
  }

  ngOnDestroy() {
    this.destroyed = true;
    if (this.loginServiceSubscription) {
      this.loginServiceSubscription.unsubscribe();
    }
    if (this.serverStatusSubscription) {
      this.serverStatusSubscription.unsubscribe();
    }
    if (this.refreshDataSubscription) {
      this.refreshDataSubscription.unsubscribe();
    }
    if (this.saveConfigurationSubscription) {
      this.saveConfigurationSubscription.unsubscribe();
    }
    if (this.changePasswordSubscription) {
      this.changePasswordSubscription.unsubscribe();
    }
    if (this.mcpConfigurationSubscription) {
      this.mcpConfigurationSubscription.unsubscribe();
    }
    if (this.mcpActionSubscription) {
      this.mcpActionSubscription.unsubscribe();
    }
    if (this.testEmailSubscription) {
      this.testEmailSubscription.unsubscribe();
    }
    if (this.mcpConfirmationSubscription) {
      this.mcpConfirmationSubscription.unsubscribe();
    }
    this.mcpUpdating = false;
    this.resetRevealedMcpToken();
  }

  refreshData(): void {
    // get the server configurations and use only first
    this.captureSnapshot();
    if (this.refreshDataSubscription) {
      this.refreshDataSubscription.unsubscribe();
    }
    this.refreshDataSubscription = this.webapiService.getServerConfigurationList().subscribe(data => {
      this.editItem = data[0];
      this.captureSnapshot();
    });
  }

  /** Normalized representation of the user-editable fields. */
  private get editableState(): any {
    return {
      network_address: this.editItem.network_address,
      ip_address: this.editItem.ip_address,
      port_internal: this.editItem.port_internal,
      host_name_external: this.editItem.host_name_external,
      port_external: this.editItem.port_external,
      local_networks: this.editItem.local_networks,
      upstream_dns_ip_address: this.editItem.upstream_dns_ip_address,
      allow_check_updates: this.editItem.allow_check_updates,
      strict_allowed_ips_in_peer_config: this.editItem.strict_allowed_ips_in_peer_config,
    };
  }

  private captureSnapshot(): void {
    this.snapshot = JSON.stringify(this.editableState);
  }

  /** True when any user-editable field differs from the originally loaded data. */
  get hasChanges(): boolean {
    return JSON.stringify(this.editableState) !== this.snapshot;
  }

  get effectiveAllowCheckUpdates(): boolean {
    return this.editItem.effective_allow_check_updates ?? this.editItem.allow_check_updates;
  }

  environmentVariableFor(field: string): string | null {
    return this.editItem.environment_overrides?.[field] ?? null;
  }

  environmentVariableLabel(field: string, label: string, environmentOverride?: boolean): string {
    const environmentVariable = this.environmentVariableNames[field];
    if (!environmentVariable) {
      return label;
    }
    const isEnvironmentOverride = environmentOverride ?? !!this.environmentVariableFor(field);
    return `${label} (${isEnvironmentOverride ? `${environmentVariable} is set` : `Managed by ${environmentVariable}`})`;
  }

  ok() {
    this.saveConfigurationSubscription = this.webapiService.saveServerConfiguration(this.editItem)
      .subscribe({
        next: data => {
          this.notification.success('Server configuration saved.');
          this.validationResult = { type: '', errors: [] } as ServerValidationError;
        },
        error: error => {
          let response = error as HttpErrorResponse;
          if (response) {
            this.validationResult = response.error as ServerValidationError;
          }
        },
        complete: () => {
          this.refreshData()
        },
      });
  }


  cancel() {
    this.refreshData();
    this.notification.warn('Server configuration reloaded from database.');
  }

  get emailStatus() {
    return this.serverStatus?.application_details?.email;
  }

  sendTestEmail(): void {
    this.testEmailSubscription = this.webapiService.sendTestEmail().subscribe({
      next: () => this.notification.success('Test e-mail sent successfully.'),
      error: error => this.notification.showEmailDeliveryFailure(this.safeEmailMessage(error?.error?.message)),
    });
  }

  private safeEmailMessage(message: unknown): string {
    const safeMessages = new Set([
      'Email authentication failed. Check the SMTP username/app password, then check the server logs for more details.',
      'The email server could not be reached. Check the SMTP host/port and network, then check the server logs for more details.',
      'Email security negotiation failed. Check the SMTP TLS/SSL settings and certificate, then check the server logs for more details.',
      'Email delivery failed. Check the SMTP settings, then check the server logs for more details.',
    ]);
    return typeof message === 'string' && safeMessages.has(message)
      ? message : 'The e-mail could not be delivered. Check the server logs for more details.';
  }

  wireguardConfiguration: WireguardConfiguration = {} as WireguardConfiguration;

  applyConfiguration(): void {
    this.webapiService.generateConfigurationFiles().subscribe(data => {
      this.notification.success('Configuration files generated on server.');
      this.webapiService.wireguardRestart().subscribe(() => {
        this.webapiService.checkServerStatus();
        this.notification.success('Wireguard restarted on server.');
      });
    });
  }

  changePassword(event: Event): void {
    if (this.changeUserPasswordInfo.new_password !== this.changeUserPasswordInfo.new_password_copy) {
      this.userSessionInfo.message = "New Passwords don't match.";
    }
    else {
      this.changePasswordSubscription = this.webapiService.changeUserPassword(this.changeUserPasswordInfo).subscribe(data => {
        this.userSessionInfo.message = data.message;
      });
    }
  }

  updateMcpConfiguration(): void {
    if (this.mcpConfigurationLoading || this.mcpLoadError || this.mcpUpdating) {
      return;
    }
    this.mcpUpdating = true;
    this.mcpActionSubscription = this.webapiService.updateMcpConfiguration(this.mcpConfiguration.mcp_enabled).subscribe({
        next: data => {
          if (this.destroyed) {
            return;
          }
          this.mcpConfiguration = data;
        this.savedMcpEnabled = data.mcp_enabled;
        this.resetRevealedMcpToken();
        this.mcpUpdating = false;
        if (data.environment_override && data.effective_enabled !== data.mcp_enabled) {
           this.notification.warn('MCP database setting saved, but WG_MCP_SERVER_ENABLED controls the effective state.');
        } else {
          this.notification.success('MCP configuration saved.');
        }
      },
      error: () => {
        if (this.destroyed) {
          return;
        }
        this.mcpConfiguration = { ...this.mcpConfiguration, mcp_enabled: this.savedMcpEnabled };
        this.mcpUpdating = false;
        this.notification.error('MCP configuration could not be saved. The previous setting was restored.');
      }
    });
  }

  generateMcpToken(): void {
    if (this.mcpConfigurationLoading || this.mcpLoadError || this.mcpUpdating) {
      return;
    }
    this.mcpUpdating = true;
    this.mcpConfirmationSubscription = this.confirmation.confirm('Generate New MCP Token', 'Existing MCP clients will stop working until their token is updated. Continue?').subscribe(confirmed => {
      if (this.destroyed) {
        return;
      }
      if (!confirmed) {
        this.mcpUpdating = false;
        return;
      }
      this.mcpActionSubscription = this.webapiService.generateMcpToken().subscribe({
        next: data => {
          if (this.destroyed) {
            return;
          }
          // The API intentionally returns the masked token after rotation. The
          // copy action fetches the same newly rotated value from its protected
          // endpoint, so the display never becomes a stale raw token.
          this.mcpConfiguration = { ...this.mcpConfiguration, ...data };
          this.resetRevealedMcpToken();
          this.notification.success('New MCP token generated.');
          this.mcpUpdating = false;
        },
        error: () => {
          if (this.destroyed) {
            return;
          }
          this.mcpUpdating = false;
          this.notification.error('MCP token could not be generated.');
        }
      });
    });
  }

  toggleMcpTokenVisibility(): void {
    if (this.mcpConfigurationLoading || this.mcpLoadError || !this.mcpConfiguration.mcp_token || this.mcpUpdating) {
      return;
    }
    if (this.mcpTokenVisible) {
      this.resetRevealedMcpToken();
      return;
    }

    this.mcpUpdating = true;
    this.mcpActionSubscription = this.webapiService.copyMcpToken().subscribe({
      next: data => {
        if (this.destroyed) {
          return;
        }
        const token = this.getRawMcpToken(data);
        if (!token) {
          this.mcpUpdating = false;
          this.notification.error('MCP token could not be shown.');
          return;
        }
        this.revealedMcpToken = token;
        this.mcpTokenVisible = true;
        this.scheduleMcpTokenHide();
        this.mcpUpdating = false;
      },
      error: () => {
        if (this.destroyed) {
          return;
        }
        this.mcpUpdating = false;
        this.notification.error('MCP token could not be shown.');
      }
    });
  }

  copyMcpToken(): void {
    if (this.mcpConfigurationLoading || this.mcpLoadError || !this.mcpConfiguration.mcp_token || this.mcpUpdating) {
      return;
    }
    this.mcpUpdating = true;
    this.mcpActionSubscription = this.webapiService.copyMcpToken().subscribe({
      next: data => {
        if (this.destroyed) {
          return;
        }
        const token = this.getRawMcpToken(data);
        if (!token) {
          if (!this.destroyed) {
            this.mcpUpdating = false;
            this.notification.error('MCP token could not be copied.');
          }
          return;
        }
        void this.copyTextToClipboard(token)
          .then(copied => {
            if (this.destroyed) {
              return;
            }
            if (copied) {
              this.notification.success('MCP token copied to clipboard.');
            } else {
              this.revealMcpTokenForManualCopy(token);
            }
          })
          .finally(() => {
            if (!this.destroyed) {
              this.mcpUpdating = false;
            }
          });
      },
      error: () => {
        if (this.destroyed) {
          return;
        }
        this.mcpUpdating = false;
        this.notification.error('MCP token could not be copied.');
      }
    });
  }

  private async copyTextToClipboard(text: string): Promise<boolean> {
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch {
        // Some browsers expose the API but reject it outside a trusted context.
      }
    }
    return this.copyTextWithTextarea(text);
  }

  private getRawMcpToken(data: { mcp_token?: unknown }): string | null {
    return typeof data?.mcp_token === 'string' && data.mcp_token.length > 0 ? data.mcp_token : null;
  }

  private copyTextWithTextarea(text: string): boolean {
    if (typeof document === 'undefined' || !document.body || !document.execCommand) {
      return false;
    }

    let textarea: HTMLTextAreaElement | null = null;
    try {
      textarea = document.createElement('textarea');
      textarea.value = text;
      textarea.setAttribute('readonly', '');
      textarea.setAttribute('aria-hidden', 'true');
      textarea.style.position = 'fixed';
      textarea.style.top = '0';
      textarea.style.left = '-9999px';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      return document.execCommand('copy');
    } catch {
      return false;
    } finally {
      if (textarea) {
        textarea.value = '';
        textarea.remove();
      }
    }
  }

  private revealMcpTokenForManualCopy(token: string): void {
    this.revealedMcpToken = token;
    this.mcpTokenVisible = true;
    this.scheduleMcpTokenHide();
    this.notification.warn('Automatic copy was blocked by browser policy. The token is selected below; press Ctrl+C (or Cmd+C) to copy it.');
    this.clearMcpTokenFocusTimer();
    this.mcpTokenFocusTimer = setTimeout(() => {
      this.mcpTokenFocusTimer = null;
      if (this.destroyed || !this.mcpTokenVisible || !this.mcpTokenInput) {
        return;
      }
      this.mcpTokenInput.nativeElement.focus();
      this.mcpTokenInput.nativeElement.select();
    });
  }

  private scheduleMcpTokenHide(): void {
    this.clearMcpTokenHideTimer();
    this.mcpTokenHideTimer = setTimeout(() => {
      this.mcpTokenHideTimer = null;
      if (!this.destroyed) {
        this.resetRevealedMcpToken();
      }
    }, 60_000);
  }

  private clearMcpTokenHideTimer(): void {
    if (this.mcpTokenHideTimer !== null) {
      clearTimeout(this.mcpTokenHideTimer);
      this.mcpTokenHideTimer = null;
    }
  }

  private clearMcpTokenFocusTimer(): void {
    if (this.mcpTokenFocusTimer !== null) {
      clearTimeout(this.mcpTokenFocusTimer);
      this.mcpTokenFocusTimer = null;
    }
  }

  private resetRevealedMcpToken(): void {
    this.clearMcpTokenHideTimer();
    this.clearMcpTokenFocusTimer();
    this.mcpTokenVisible = false;
    this.revealedMcpToken = null;
  }

}
