# WireGuard UI Plus

WireGuard UI Plus is a Dockerized web UI for running and managing a WireGuard
VPN. The Angular single-page application and Django REST API run together in one
container, which also generates WireGuard configuration and related iptables
rules.

> **Disclaimer:** Use this software at your own risk. It was developed for
> personal use at home and is shared in the hope that it is useful to others.

## Overview

![VPN Layout showing peer, peer-group, and target relationships](./images/wg-ui-plus-vpn-layout.png)

## Why this project?

WireGuard UI Plus is designed for home and small-network VPNs where different
clients need different access. Instead of maintaining fine-grained iptables
rules by hand, define resources as targets, put clients into peer groups, and
associate targets with those groups.

## Key features

- Manage WireGuard clients (**peers**), peer groups, and resource **targets**.
- Grant or revoke access through peer-group/target relationships.
- Generate peer configurations, QR codes, `.conf` downloads, and optional e-mail.
- Configure full-tunnel or narrower relationship-based `AllowedIPs` behavior.
- Apply generated WireGuard configuration and monitor peer status and iptables.
- Visualize relationships in **VPN Layout**.
- Responsive dark/light Angular UI and support for Raspberry Pi and other
  single-board computers.
- Optional Streamable HTTP MCP server support, disabled by default.

## Quick start

You need Docker and a host that can grant the container `NET_ADMIN` and
`SYS_MODULE`, set the required IPv4 sysctls, and access host kernel modules.

1. Create the persistent directories:

   ```bash
   mkdir -p ./config ./data
   ```

   Ensure that these directories are writable by the container runtime user.

2. Start the image (this example publishes host UDP `1196` to the default
   container WireGuard UDP port `51820` and the UI on TCP `8000`):

   ```bash
   docker run -it --rm \
     --cap-add NET_ADMIN --cap-add SYS_MODULE \
     --sysctl net.ipv4.conf.all.src_valid_mark=1 \
     --sysctl net.ipv4.ip_forward=1 \
     -v "${PWD}/data":/data -v "${PWD}/config":/config \
     -v /lib/modules:/lib/modules:ro \
     --tmpfs /tmp:rw,nosuid,nodev,noexec \
     -p "1196:51820/udp" -p "8000:8000" \
     ghcr.io/vijaygill/wg-ui-plus:latest
   ```

3. Forward the selected UDP port from the router to the WireGuard host and open
   `http://<internal-host-ip>:8000`.
4. Log in with `admin` / `admin` and immediately change the password in
   **Server Configuration** → **Change Password**.
5. Set **Host Name External** and **Upstream DNS Server**, review **Local
   Networks**, then select **Apply Changes**.
6. Open a peer, scan its QR code with the WireGuard client, and configure access
   using [ACCESS_CONTROL.md](./ACCESS_CONTROL.md).

The container-local `/tmp` tmpfs provides temporary working space without
exposing the host's `/tmp` to the container. It is intentionally non-persistent
and uses `nosuid`, `nodev`, and `noexec`; do not replace it with a host `/tmp`
bind mount unless a specific local development integration requires that broader
host access.

For persistent Compose deployment, start with
[docker-compose-example.yml](./docker-compose-example.yml) and read
[DEPLOYMENT.md](./DEPLOYMENT.md) first. The example maps host UDP `1195` to
the default container UDP `51820` but does not set `WG_PORT_EXTERNAL` (default
`1196`). Add `WG_PORT_EXTERNAL=1195` or change the mapping so peer
configurations, router forwarding, and the application agree. The example also
enables `CORS_ALLOW_ALL_ORIGINS=true` for convenience; restrict it before
deployment.

## Sending tunnel information using email

The application can send a peer's current WireGuard configuration by SMTP. SMTP
configuration is supplied through environment variables when the container
starts; it is not entered in the peer form. Use the following steps.

1. **Choose an SMTP account.** For Gmail, enable two-step verification and
   create an app password. Use the app password rather than the normal Gmail
   account password. Other providers require their own SMTP host, port, and
   authentication requirements.

2. **Set the SMTP environment variables.** The minimum configuration requires
   `EMAIL_HOST`, `EMAIL_PORT`, and `EMAIL_DEFAULT_FROM_EMAIL`. Username and
   password are optional, but must be supplied together when used. TLS and SSL
   are optional and default to false; they cannot both be enabled. This supports
   an unauthenticated local Postfix server:

   Boolean values are case-insensitive and may be written as `true`, `1`,
   `yes`, or `on`, or as `false`, `0`, `no`, or `off`. TLS and SSL must not both
    be enabled. For local Postfix, use:

   ```text
    EMAIL_HOST=mail.local
    EMAIL_PORT=25
    EMAIL_DEFAULT_FROM_EMAIL=wg-ui-plus@mail.local
    EMAIL_USE_SSL=False
    EMAIL_USE_TLS=False
    ```

    Authenticated Gmail/app-password SMTP remains supported:

    ```text
    EMAIL_HOST=smtp.gmail.com
    EMAIL_HOST_USER=your-account@gmail.com
    EMAIL_HOST_PASSWORD=your-gmail-app-password
    EMAIL_PORT=587
    EMAIL_USE_TLS=True
    EMAIL_USE_SSL=False
    EMAIL_DEFAULT_FROM_EMAIL=your-account@gmail.com
    ```

3. **Pass the values to Docker.** Prefer a protected env file for SMTP
   credentials. Create `./email.env` with the placeholder values below, make the
   file readable only by the account that needs it, and exclude it from source
   control (for example, use `chmod 600 ./email.env`):

   ```text
    EMAIL_HOST=mail.local
    EMAIL_PORT=25
    EMAIL_USE_TLS=False
    EMAIL_USE_SSL=False
    EMAIL_DEFAULT_FROM_EMAIL=wg-ui-plus@mail.local
   ```

   For a one-off `docker run`, add `--env-file ./email.env` to the **full
   Quick Start `docker run` command**; the SMTP-only example below is complete
   and retains the required WireGuard capabilities, mounts, ports, and tmpfs:

   ```bash
   docker run -it --rm \
     --env-file ./email.env \
     --cap-add NET_ADMIN --cap-add SYS_MODULE \
     --sysctl net.ipv4.conf.all.src_valid_mark=1 \
     --sysctl net.ipv4.ip_forward=1 \
     -v "${PWD}/data":/data -v "${PWD}/config":/config \
     -v /lib/modules:/lib/modules:ro \
     --tmpfs /tmp:rw,nosuid,nodev,noexec \
     -p "1196:51820/udp" -p "8000:8000" \
     ghcr.io/vijaygill/wg-ui-plus:latest
   ```

   With Compose, use the same protected env file through `env_file`:

   ```yaml
   services:
     wireguard:
       env_file:
         - ./email.env
   ```

   Do not commit the env file, SMTP password, or other credentials to source
   control, and do not put them in logs or screenshots. Use your deployment
   platform's secret or environment-variable mechanism where available. Inline
   `--env EMAIL_HOST_PASSWORD=...` options may be exposed through shell history,
   Docker metadata, or operational tooling, so use them only as illustrative
   examples or for a controlled test. The checked-in
   `docker-compose-example.yml` contains placeholders only.

4. **Restart or recreate the container.** Environment variables are read by the
   running process at startup. For Compose, recreate the service after changing
   them, for example `docker compose up -d --force-recreate wireguard`. A plain
   `docker restart` does not replace the environment stored in an existing
   container. For `docker run`, stop and remove the old container and create it
   again with the updated `--env-file`.

5. **Test SMTP from the server configuration page.** Open **Server Configuration**
   and select **Send Test Email**. The authenticated action sends a simple message
   from `EMAIL_DEFAULT_FROM_EMAIL` to that same address; it never accepts an
   arbitrary test recipient and includes no peer or QR data.

6. **Save the recipient on the peer.** In the web UI, open the peer, enter its
   e-mail address, and save the peer. The send action uses only this saved
   database address. It does not accept an alternate recipient address in the
   button action or request, so verify the address before sending.

7. **Send the configuration.** With SMTP configured and a saved peer address,
   open the peer and select **Send Config By Email**. Confirm the action. At send
   time the server generates the current `.conf` and QR image and attaches both
   to the message; it does not use a configuration or QR attachment supplied by
   the caller.

8. **Verify delivery.** A successful action means the SMTP backend accepted the
   message for sending. It does not prove that the message reached the final
   inbox. Check the recipient's spam/quarantine folders and the provider's mail
   logs as well as the application notification.

### Email troubleshooting

- If the button is unavailable, read the displayed SMTP status explanation and
  check that all required variables are present in the container, that their
  names are exact, and that the container was recreated after they changed.
- An invalid port, boolean value, sender address, partial username/password pair,
  or combination of TLS and SSL causes the SMTP configuration to be rejected.
  Use a numeric port, accepted boolean forms, and supply credentials together.
- For Gmail authentication failures, confirm that two-step verification is
  enabled and that `EMAIL_HOST_PASSWORD` is an app password. Confirm the account
  username and sender address are valid, and that the container can reach
  `smtp.gmail.com:587`.
- Confirm the peer's saved e-mail address is valid. The server will not send to
  an address supplied separately from the peer record.
- If SMTP accepts the message but it is not visible, inspect spam/quarantine and
  provider delivery logs. A provider may accept a message and later defer or
  reject it; application success alone cannot establish inbox delivery.
- Review container logs for the provider's connection or authentication error,
  but redact passwords, app passwords, tokens, and message contents before
  sharing logs.

## How Traffic Flows Through WireGuard UI Plus

The following diagram uses **sample/example values only** to show how a peer
reaches a target through WireGuard UI Plus. The peer and target names, host
names, IP addresses, and ports are illustrative and must be replaced with the
values from your network.

```text
  External / public side (sample values)

  Alice's Laptop (sample peer)
  VPN address: 10.8.0.2 (sample)
          │
          │  Encrypted WireGuard tunnel to the sample router endpoint
          │  Endpoint: 203.0.113.10:1196/UDP (sample)
          ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ Your ISP's Router/Modem                                      │
  │ WAN/external IP: 203.0.113.10 (documentation-only sample)    │
  │ External WireGuard port: UDP 1196 (sample)                   │
  │                                                              │
  │ Port forwarding: 203.0.113.10:1196/UDP                       │
  │                  ───────────────► 192.168.1.10:51820/UDP     │
  └──────────────────────────────────────────────────────────────┘
          │
          │  Internal LAN (sample)
          ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ WireGuard UI Plus machine (sample host)                      │
  │ Internal IP: 192.168.1.10 (sample)                           │
  │ Internal WireGuard port: UDP 51820 (default; sample)         │
  │ Web UI: TCP 8000 (sample)                                    │
  │ VPN address: 10.8.0.1 (sample)                               │
  └──────────────────────────────────────────────────────────────┘
          │
          │  Allowed traffic for Alice's sample peer
          ▼
  ┌──────────────────────────────────────────────────────────────┐
  │ Sample target: NAS                                           │
  │ Internal address: 192.168.1.50 (sample)                      │
  │ Allowed target ports: TCP 139 and TCP 445 (sample)           │
  └──────────────────────────────────────────────────────────────┘
```

`203.0.113.10` is reserved for documentation examples and is not a real
address to configure. Your router's actual public IP or DNS name, external
WireGuard port, internal host IP, VPN addresses, and target address depend on
your network. The **external port** (`UDP 1196` in this example) is the
router-facing port used by peer endpoints and forwarded by the router. The
**internal WireGuard port** (`UDP 51820` by default) is the port where the
WireGuard UI Plus host receives the forwarded traffic. The NAS's **target
ports** (`TCP 139` and `TCP 445` in this example) are separate application
ports allowed after the VPN connection is established; they are not
WireGuard listener ports.

## Documentation

- [FAQ](./FAQ.md) — answers about installation, configuration, access, routing,
  troubleshooting, authentication, MCP, e-mail, updates, backups, and security.
- [Access control](./ACCESS_CONTROL.md) — peers, peer groups, targets,
  relationships, examples, `AllowedIPs`, and applying changes.
- [Deployment](./DEPLOYMENT.md) — Docker/Compose, ports, volumes, privileges,
  environment settings, backups, upgrades, and secure exposure.
- [Development](./DEVELOPMENT.md) — development shell, Angular/backend builds,
  tests, and contributor commands.
- [MCP server](./MCP.md) — MCP administration, authentication, tools, and
  transport details.

Issues and pull requests are welcome. See [DEVELOPMENT.md](./DEVELOPMENT.md)
before working on the project.
