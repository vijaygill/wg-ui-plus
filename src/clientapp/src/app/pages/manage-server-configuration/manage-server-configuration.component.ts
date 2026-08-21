import { ChangeDetectionStrategy, Component, ElementRef, OnDestroy, OnInit, ViewChild, ChangeDetectorRef, effect } from '@angular/core';
import { ChangeUserPasswordInfo, EmailConfiguration, McpConfiguration, ServerConfiguration, ServerStatus, ServerValidationError, UserSessionInfo, WireguardConfiguration } from '../../webapi.entities';

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

  /** Feedback message shown on the Change Password tab. */
  passwordChangeMessage = '';

  refreshDataSubscription !: Subscription;
  mcpConfigurationSubscription !: Subscription;
  mcpActionSubscription !: Subscription;
  testEmailSubscription !: Subscription;
  mcpConfirmationSubscription !: Subscription;
  saveConfigurationSubscription !: Subscription;
  changePasswordSubscription !: Subscription;
  emailConfigurationSubscription !: Subscription;
  emailActionSubscription !: Subscription;
  emailConnectivitySubscription !: Subscription;
  mcpConfiguration: McpConfiguration = {} as McpConfiguration;
  mcpLoadError = '';
  mcpConfigurationLoading = true;
  mcpUpdating = false;
  mcpTokenVisible = false;
  revealedMcpToken: string | null = null;
  emailConfiguration: EmailConfiguration = {} as EmailConfiguration;
  emailLoadError = '';
  emailConfigurationLoading = true;
  emailUpdating = false;
  /** Per-field API validation errors (DRF format: { field: [message] }). */
  emailValidationErrors: { [field: string]: string[] } = {};
  private emailSnapshot = '';
  private savedMcpEnabled = false;
  private mcpTokenHideTimer: ReturnType<typeof setTimeout> | null = null;
  private mcpTokenFocusTimer: ReturnType<typeof setTimeout> | null = null;
  private destroyed = false;

  /** Previous server status seen by the reload effect (null until its first run). */
  private previousStatus: ServerStatus | null = null;

  /**
   * Reloads the editable configuration whenever the server reports that the
   * database changed (last_db_change_datetime advanced between polls). The
   * seeded placeholder carries no timestamp, so the eager load in ngOnInit
   * remains the initial fetch.
   */
  private readonly reloadOnDbChange = effect(() => {
    const status = this.webapiService.serverStatus();
    const previous = this.previousStatus;
    this.previousStatus = status;
    if (previous?.last_db_change_datetime
      && status.last_db_change_datetime
      && previous.last_db_change_datetime < status.last_db_change_datetime) {
      this.refreshData();
    }
  });

  /** Last session value seen by the redirect effect (null until its first run). */
  private lastSeenSession: UserSessionInfo | null = null;

  /**
   * Redirects to the login page whenever the session turns logged-out.
   * The seeded placeholder is skipped so an authenticated user opening this
   * page is not redirected before the authentication check lands.
   */
  private readonly sessionRedirect = effect(() => {
    const session = this.loginService.userSessionInfo();
    const seen = this.lastSeenSession;
    this.lastSeenSession = session;
    if (seen !== null && !session.is_logged_in) {
      this.router.navigate(['/login']);
    }
  });

  private readonly environmentVariableNames: { [field: string]: string } = {
    network_address: 'WG_NETWORK_ADDRESS',
    host_name_external: 'WG_HOST_NAME_EXTERNAL',
    local_networks: 'WG_LOCAL_NETWORKS',
    upstream_dns_ip_address: 'WG_UPSTREAM_DNS_SERVER',
    port_external: 'WG_PORT_EXTERNAL',
    port_internal: 'WG_PORT_INTERNAL',
     strict_allowed_ips_in_peer_config: 'WG_STRICT_ALLOWED_IPS_IN_PEER_CONFIG',
     allow_check_updates: 'WG_ALLOW_CHECK_UPDATES',
     mcp_server_enabled: 'WG_MCP_SERVER_ENABLED',
     email_host: 'EMAIL_HOST',
     email_port: 'EMAIL_PORT',
     email_host_user: 'EMAIL_HOST_USER',
     email_host_password: 'EMAIL_HOST_PASSWORD',
     email_default_from_email: 'EMAIL_DEFAULT_FROM_EMAIL',
     email_use_tls: 'EMAIL_USE_TLS',
     email_use_ssl: 'EMAIL_USE_SSL'
  };

  @ViewChild('mcpTokenInput') private mcpTokenInput?: ElementRef<HTMLInputElement>;


  constructor(private notification: NotificationService,
    private webapiService: WebapiService,
    private router: Router, private loginService: LoginService, private confirmation: ConfirmationDialogService,
    private cdr: ChangeDetectorRef) { }

  ngOnInit(): void {
    this.loginService.checkIsUserAuthenticated();
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
        this.cdr.markForCheck();
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
        this.cdr.markForCheck();
      }
    });
    this.loadEmailConfiguration();
  }

  ngOnDestroy() {
    this.destroyed = true;
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
    if (this.emailConfigurationSubscription) {
      this.emailConfigurationSubscription.unsubscribe();
    }
    if (this.emailActionSubscription) {
      this.emailActionSubscription.unsubscribe();
    }
    if (this.emailConnectivitySubscription) {
      this.emailConnectivitySubscription.unsubscribe();
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
      this.cdr.markForCheck();
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
          this.cdr.markForCheck();
        },
        error: error => {
          let response = error as HttpErrorResponse;
          if (response) {
            this.validationResult = response.error as ServerValidationError;
            this.cdr.markForCheck();
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
    return this.webapiService.serverStatus().application_details?.email;
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
      'The test email could not be delivered. Check the server logs for more details.',
      'SMTP email is not configured. Set EMAIL_HOST, EMAIL_PORT, and EMAIL_DEFAULT_FROM_EMAIL.',
      'SMTP email is not configured. Set EMAIL_HOST and EMAIL_PORT.',
      'The SMTP host name could not be resolved. Check EMAIL_HOST.',
      'The SMTP server did not respond. Check the host and port, and that the port is reachable from the container (for Docker, check the port mapping).',
      'The connection to the SMTP server was refused. Check the host, port, and firewall or Docker port mapping.',
      'The SMTP server could not be checked. Check the server logs for more details.',
    ]);
    return typeof message === 'string' && safeMessages.has(message)
      ? message : 'The email server operation failed. Check the server logs for more details.';
  }

  testEmailConnectivity(): void {
    this.emailConnectivitySubscription = this.webapiService.testEmailConnectivity().subscribe({
      next: result => this.notification.success(result?.message ?? 'SMTP server is reachable.'),
      error: error => this.notification.showEmailDeliveryFailure(this.safeEmailMessage(error?.error?.message)),
    });
  }

  /** Normalized representation of the editable email fields. */
  private get editableEmailState(): any {
    return {
      email_host: this.emailConfiguration.email_host,
      email_port: this.emailConfiguration.email_port,
      email_host_user: this.emailConfiguration.email_host_user,
      email_host_password: this.emailConfiguration.email_host_password ?? '',
      email_default_from_email: this.emailConfiguration.email_default_from_email,
      email_use_tls: this.emailConfiguration.email_use_tls,
      email_use_ssl: this.emailConfiguration.email_use_ssl,
    };
  }

  private captureEmailSnapshot(): void {
    this.emailSnapshot = JSON.stringify(this.editableEmailState);
  }

  /** True when any editable email field differs from the originally loaded data. */
  get emailHasChanges(): boolean {
    return JSON.stringify(this.editableEmailState) !== this.emailSnapshot;
  }

  emailEnvironmentVariableFor(field: string): string | null {
    return this.emailConfiguration?.environment_overrides?.[field] ?? null;
  }

  /** Single security-mode value derived from the two SMTP security booleans. */
  get emailSecurityMode(): 'none' | 'tls' | 'ssl' {
    if (this.emailConfiguration.email_use_tls) {
      return 'tls';
    }
    if (this.emailConfiguration.email_use_ssl) {
      return 'ssl';
    }
    return 'none';
  }

  set emailSecurityMode(mode: 'none' | 'tls' | 'ssl') {
    this.emailConfiguration.email_use_tls = mode === 'tls';
    this.emailConfiguration.email_use_ssl = mode === 'ssl';
  }

  /** Radio option label naming the governing environment variable(s). */
  emailSecurityOptionLabel(mode: 'none' | 'tls' | 'ssl'): string {
    const tls = this.emailEnvironmentVariableFor('email_use_tls');
    const ssl = this.emailEnvironmentVariableFor('email_use_ssl');
    const tlsVariable = this.environmentVariableNames['email_use_tls'];
    const sslVariable = this.environmentVariableNames['email_use_ssl'];
    if (mode === 'tls') {
      return `TLS (STARTTLS) (${tls ? `${tlsVariable} is set` : `Managed by ${tlsVariable}`})`;
    }
    if (mode === 'ssl') {
      return `SSL (${ssl ? `${sslVariable} is set` : `Managed by ${sslVariable}`})`;
    }
    // None is only meaningful (and selectable) while neither variable is set.
    return tls || ssl
      ? 'None'
      : `None (Managed by ${tlsVariable} and ${sslVariable})`;
  }

  /** Static help text explaining the SMTP security environment variables. */
  get emailSecurityHelpText(): string {
    return 'SMTP security is controlled by the EMAIL_USE_TLS and EMAIL_USE_SSL environment variables. ' +
      'A variable is considered set only when its value is true; unset or false means it does not apply. ' +
      'Only one can be true at a time: None means both are false or unset, TLS (STARTTLS) means EMAIL_USE_TLS=true, ' +
      'SSL means EMAIL_USE_SSL=true.';
  }

  /** State-specific guidance shown when a security variable is set to true. */
  get emailSecurityEnvironmentMessage(): string {
    const tls = this.emailEnvironmentVariableFor('email_use_tls');
    const ssl = this.emailEnvironmentVariableFor('email_use_ssl');
    if (tls && ssl) {
      return `${tls} and ${ssl} are set to true, so the security mode is managed by the environment and cannot be changed here. Set both to false or unset them to manage the security mode from this page.`;
    }
    if (tls) {
      return `${tls} is set to true, so the security mode is managed by the environment and cannot be changed here. Set it to false or unset it to manage the security mode from this page.`;
    }
    if (ssl) {
      return `${ssl} is set to true, so the security mode is managed by the environment and cannot be changed here. Set it to false or unset it to manage the security mode from this page.`;
    }
    return '';
  }

  /** Effective status from the email configuration payload (fresh, per-field merged). */
  get emailEffectiveStatus(): { status: 'configured' | 'invalid' | 'unavailable'; message: string } | null {
    return this.emailConfiguration.effective ?? null;
  }

  /** First validation error for a field ('' when the field is valid). */
  emailFieldError(field: string): string {
    const messages = this.emailValidationErrors[field];
    return messages && messages.length > 0 ? messages[0] : '';
  }

  private emptyEmailConfiguration(): EmailConfiguration {
    return {
      email_host: '',
      email_port: null,
      email_host_user: '',
      email_password_set: false,
      email_default_from_email: '',
      email_use_tls: false,
      email_use_ssl: false,
      email_host_password: '',
      environment_overrides: {},
      effective: { status: 'unavailable', message: '' },
    };
  }

  private applyEmailConfiguration(data: EmailConfiguration): void {
    this.emailConfiguration = { ...data, email_host_password: '' };
    this.emailValidationErrors = {};
    this.captureEmailSnapshot();
  }

  private loadEmailConfiguration(): void {
    this.emailConfigurationLoading = true;
    if (this.emailConfigurationSubscription) {
      this.emailConfigurationSubscription.unsubscribe();
    }
    this.emailConfigurationSubscription = this.webapiService.getEmailConfiguration().subscribe({
      next: data => {
        if (this.destroyed) {
          return;
        }
        this.applyEmailConfiguration(data);
        this.emailConfigurationLoading = false;
        this.emailLoadError = '';
        this.cdr.markForCheck();
      },
      error: () => {
        if (this.destroyed) {
          return;
        }
        this.emailLoadError = 'Email settings could not be loaded. Refresh after signing in again.';
        this.emailConfigurationLoading = false;
        this.emailConfiguration = this.emptyEmailConfiguration();
        this.cdr.markForCheck();
      }
    });
  }

  saveEmailConfiguration(): void {
    if (this.emailConfigurationLoading || this.emailLoadError || this.emailUpdating || !this.emailHasChanges) {
      return;
    }
    this.emailUpdating = true;
    this.emailValidationErrors = {};

    const port = this.emailConfiguration.email_port;
    if (port !== null && (typeof port !== 'number' || !Number.isInteger(port) || port < 1 || port > 65535)) {
      this.emailValidationErrors = {
        email_port: ['EMAIL_PORT must be between 1 and 65535.'],
      };
      this.emailUpdating = false;
      return;
    }

    // Only non-environment-controlled fields are sent, so a partial
    // environment (e.g. EMAIL_USE_TLS set) cannot block saving the rest.
    const overrides = this.emailConfiguration.environment_overrides ?? {};
    const payload = {} as EmailConfiguration;
    if (!overrides['email_host']) {
      payload.email_host = this.emailConfiguration.email_host;
    }
    if (!overrides['email_port']) {
      payload.email_port = this.emailConfiguration.email_port;
    }
    if (!overrides['email_host_user']) {
      payload.email_host_user = this.emailConfiguration.email_host_user;
    }
    if (!overrides['email_host_password']) {
      // Blank keeps the stored password; only a typed replacement is sent.
      const password = this.emailConfiguration.email_host_password ?? '';
      if (password) {
        payload.email_host_password = password;
      }
    }
    if (!overrides['email_default_from_email']) {
      payload.email_default_from_email = this.emailConfiguration.email_default_from_email;
    }
    if (!overrides['email_use_tls']) {
      payload.email_use_tls = this.emailConfiguration.email_use_tls;
    }
    if (!overrides['email_use_ssl']) {
      payload.email_use_ssl = this.emailConfiguration.email_use_ssl;
    }
    this.emailActionSubscription = this.webapiService.updateEmailConfiguration(payload).subscribe({
      next: data => {
        if (this.destroyed) {
          return;
        }
        this.applyEmailConfiguration(data);
        this.emailUpdating = false;
        this.notification.success('Email settings saved.');
        this.webapiService.checkServerStatus();
        this.cdr.markForCheck();
      },
      error: error => {
        if (this.destroyed) {
          return;
        }
        this.emailUpdating = false;
        const response = error as HttpErrorResponse;
        if (response?.status === 400 && response.error && typeof response.error === 'object') {
          // Per-field backend validation: keep Save enabled so edits are kept.
          this.emailValidationErrors = response.error as { [field: string]: string[] };
        } else {
          this.emailValidationErrors = {};
          this.notification.error('Email settings could not be saved.');
        }
        this.cdr.markForCheck();
      }
    });
  }

  cancelEmailConfiguration(): void {
    this.loadEmailConfiguration();
    this.notification.warn('Email settings reloaded from database.');
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
      this.passwordChangeMessage = "New Passwords don't match.";
    }
    else {
      this.changePasswordSubscription = this.webapiService.changeUserPassword(this.changeUserPasswordInfo).subscribe(data => {
        this.passwordChangeMessage = data.message;
        this.cdr.markForCheck();
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
        this.cdr.markForCheck();
      },
      error: () => {
        if (this.destroyed) {
          return;
        }
        this.mcpConfiguration = { ...this.mcpConfiguration, mcp_enabled: this.savedMcpEnabled };
        this.mcpUpdating = false;
        this.notification.error('MCP configuration could not be saved. The previous setting was restored.');
        this.cdr.markForCheck();
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
        this.cdr.markForCheck();
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
          this.cdr.markForCheck();
        },
        error: () => {
          if (this.destroyed) {
            return;
          }
          this.mcpUpdating = false;
          this.notification.error('MCP token could not be generated.');
          this.cdr.markForCheck();
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
          this.cdr.markForCheck();
          return;
        }
        this.revealedMcpToken = token;
        this.mcpTokenVisible = true;
        this.scheduleMcpTokenHide();
        this.mcpUpdating = false;
        this.cdr.markForCheck();
      },
      error: () => {
        if (this.destroyed) {
          return;
        }
        this.mcpUpdating = false;
        this.notification.error('MCP token could not be shown.');
        this.cdr.markForCheck();
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
            this.cdr.markForCheck();
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
            this.cdr.markForCheck();
          })
          .finally(() => {
            if (!this.destroyed) {
              this.mcpUpdating = false;
              this.cdr.markForCheck();
            }
          });
      },
      error: () => {
        if (this.destroyed) {
          return;
        }
        this.mcpUpdating = false;
        this.notification.error('MCP token could not be copied.');
        this.cdr.markForCheck();
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
        this.cdr.markForCheck();
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
