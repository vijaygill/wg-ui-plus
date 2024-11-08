export interface UserCrendentials {
    username: string;
    password: string;
}

export interface UserSessionInfo {
    is_logged_in: boolean;
    message: string;
}

export interface ChangeUserPasswordInfo {
    current_password: string;
    new_password: string;
    new_password_copy: string;
}

export interface Entity {
    id: number;
}

export interface Peer extends Entity {
    name: string;
    description: string;
    email_address: string;
    ip_address: string;
    port: number;
    disabled: boolean;
    public_key: string;
    private_key: string;
    peer_configuration: string;
    peer_groups: PeerGroup[];
    peer_groups_lookup: PeerGroup[];
    peer_group_ids: number[];
    qr: string;
    target_names: string;
    configuration: string;
}

export interface PeerGroup extends Entity {
    name: string;
    description: string;
    disabled: boolean;
    allow_modify_self: boolean;
    allow_modify_peers: boolean;
    allow_modify_targets: boolean;
    targets: Target[];
    targets_lookup: Target[];
    peers: Peer[];
    peers_lookup: Peer[];
    peer_ids: number[];
    target_ids: number[];
    target_names: string;
    is_everyone_group: boolean;
}

export interface Target extends Entity {
    name: string;
    description: string;
    ip_address: string;
    disabled: boolean;
    allow_modify_self: boolean;
    allow_modify_peer_groups: boolean;
    peer_groups: PeerGroup[];
    peer_groups_lookup: PeerGroup[];
    peer_group_ids: number[];
}

export interface ServerConfiguration {
    id: number;
    network_address: string;
    host_name_external: string;
    port_internal: number;
    port_external: number;
    local_networks: string;
    wireguard_config_path: string;
    script_path_post_down: string;
    script_path_post_up: string;
    public_key: string;
    private_key: string;
    peer_default_port: number;
    upstream_dns_ip_address: string;
    allow_check_updates: boolean;
}

export interface WireguardConfiguration {
    server_configuration: string;
    peer_configurations: string[];
}


export interface ServerValidationError {
    type: string;
    errors: ServerValidationErrorItem[];
}

export interface ServerValidationErrorItem {
    code: string;
    detail: string;
    attr: string;
}

export interface ConnectedPeerInformation {
    datetime: string;
    message: string;
    items: ConnectedPeerInformationItem[];
}

export interface ConnectedPeerInformationItem {
    peer_name: string;
    status: string;
    interface: string;
    public_key: string;
    preshared_key: string;
    end_point: string;
    end_point_ip: string;
    end_point_port: string;
    allowed_ips: string;
    allowed_ips_ip: string;
    allowed_ips_mask: string;
    latest_handshake: string;
    transfer_rx: number;
    transfer_tx: number;
    persistent_keepalive: number;
}

export interface LicenseInfo {
    license: string;
}

export interface ApplicationDetails {
    current_time: Date;
    latest_live_version: string;
    current_version: string;
    allow_allow_check_updates: boolean;
    is_email_enabled: boolean;
}

export interface IpTablesLog {
    status: string;
    datetime: string;
    output: string;
}

export interface ServerStatus {
    status: string;
    message: string;
    hostname: string;
    platform: string;
    platform_version: string;
    platform_system: string;
    platform_processor: string;
    platform_architecture: string;
    need_regenerate_files: boolean;
    last_db_change_datetime: Date;
    last_file_change_datetime: Date;
    application_details: ApplicationDetails;
}

export interface PlatformInformation {
    is_small_screen: boolean;
}