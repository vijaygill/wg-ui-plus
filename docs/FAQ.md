# Frequently asked questions

## What is WireGuard UI Plus?

It is a Dockerized Angular and Django application for managing a WireGuard VPN,
its peer configurations, and access rules generated from peer groups and targets.
It is intended primarily for home and small-network deployments.

## How do I install it?

Install Docker, create persistent `config` and `data` directories, and run the
image with `NET_ADMIN`, `SYS_MODULE`, the required IPv4 sysctls, `/lib/modules`,
and the two persistent mounts. The concise command is in [README.md](../README.md);
full Docker and Compose guidance is in [DEPLOYMENT.md](./DEPLOYMENT.md).

By default, the container listens on UDP `51820` internally and TCP `8000` for
the UI. If `WG_PORT_INTERNAL` changes, update the container-side Docker port
mapping. The Docker host port and router forwarding normally remain unchanged;
change them only if you also choose a different host or router-facing port. The
router-facing external UDP port must match `WG_PORT_EXTERNAL`, because that is
the port written into generated peer endpoints. The Docker host port may differ
when the router forwards one external port to another host port.

## What is the default login?

The initial credentials are `admin` / `admin`. Change the password immediately in
**Server Configuration** → **Change Password**, and do not expose the UI publicly
with the default password.

## What should I configure first?

In **Server Configuration**, review **Network Address**, **Host Name External**,
**Port External**, **Port Internal**, **Upstream DNS Server**, and **Local
Networks**. Save the settings and select **Apply Changes**. The external host name
is the public IP or DNS name clients use; the internal server IP is assigned by
the application.

## What do peer, peer group, and target mean?

A **peer** is a client device and its WireGuard identity. A **peer group** contains
peers. A **target** is a resource, such as a host, selected host ports, or a
network. Associating targets with peer groups grants access; for server-side
generated access rules, a peer inherits targets from its enabled groups and only
enabled targets are included. Disabled objects can still leave routes in a
strict client configuration until an updated peer configuration is distributed.
See [ACCESS_CONTROL.md](./ACCESS_CONTROL.md) for the complete model and examples.

## What are `EveryOne` and `Internet`?

`EveryOne` and the built-in `Internet` target are created during initialization.
`EveryOne` is handled as a special global default during configuration generation,
so its targets can apply to all peers even when editable memberships do not show
an explicit `EveryOne` entry. Remove the `Internet` association from `EveryOne` if
that default is too broad. These names are case-sensitive UI terminology.

## How do I allow access to one service?

Create a peer group, add the relevant peer, create a target such as
`192.168.0.51:139,445`, and associate the target with that group. Verify the
relationship under **VPN Layout**, select **Apply Changes**, and distribute the
peer's updated QR code or `.conf` file.

![Peer QR code screen for adding a WireGuard client](../images/wg-ui-plus-peer-qr.png)

## How do targets represent networks and ports?

Targets accept a host (`192.168.0.51`), a network (`192.168.0.0/24`), or a host
with one or more comma-separated ports (`192.168.0.51:139,445`). A target is not
a DNS name or arbitrary URL. Disable a target to suspend it without deleting its
relationships.

## How does `AllowedIPs` work?

Normal generated peer configurations use `0.0.0.0/0`, routing IPv4 traffic into
the tunnel. The server's generated rules still control which targets the peer may
reach. Enable **Strict AllowedIPs in Peer Config** in **Server Configuration** to
narrow generated routes based on the peer's relationships. The result can also
include required VPN/peer addresses and can fall back to `0.0.0.0/0` when no
route is calculated. Changes to group/target relationships may then require a
new client configuration.

If `Internet` is a full-tunnel target, put protected LAN ranges in **Local
Networks** so they are not accidentally treated as part of Internet access.
Add explicit targets for LAN access that should be allowed.

## When do changes take effect?

Database edits are saved first. Select **Apply Changes** after access or server
configuration changes to regenerate WireGuard configuration and related iptables
rules and restart the VPN. Affected clients may also need a newly distributed
configuration, especially after key, endpoint, VPN address, or strict
`AllowedIPs` changes.

## Where can I inspect the current state?

**Monitor Peers** shows handshake and transfer information for peers.
**Monitor IP-Tables** shows relevant chains and counters. **VPN Layout** shows
peer, peer group, and target relationships. These views help distinguish a client
handshake problem from an access-rule problem.

![Monitor Peers showing handshake and transfer status](../images/wg-ui-plus-monitor-peers.png)

![Monitor IP-Tables showing generated chains and counters](../images/wg-ui-plus-monitor-iptables.png)

## A peer cannot connect. What should I check?

Check that the router forwards the correct UDP port, the external host name and
port match the generated client file, and the container has WireGuard privileges.
Confirm the client has the current QR/configuration, then inspect **Monitor
Peers** for a recent handshake. Check container logs and the generated
`/config/wireguard/wg0.conf`; do not paste private keys into issue reports.

## A peer connects but cannot reach a target. What should I check?

Confirm the peer belongs to the intended peer group and the target is associated
with that group. Ensure neither is disabled, inspect **VPN Layout**, then select
**Apply Changes**. Check **Monitor IP-Tables**, target address/port syntax,
`Local Networks`, local routing, and the destination host firewall. If strict
`AllowedIPs` is enabled, distribute the updated client configuration.

## How is authentication handled?

The web UI uses the application login. Change the initial password and use HTTPS
and a reverse proxy for remote access. The MCP endpoint uses its own application-
managed token; it is not a low-privilege per-user API boundary.

## How do I enable MCP?

MCP is disabled by default. Set `WG_MCP_SERVER_ENABLED=true` (also accepted:
`1`, `yes`, `y`, `on`) at startup, or use the **MCP Server** tab when no
environment override is present. `false`, `0`, `no`, `n`, and `off` disable it;
other values are rejected. The Streamable HTTP endpoint is `/mcp`; use
`Authorization: Bearer <token>` (legacy `Token` is also accepted). See
[MCP.md](./MCP.md) for commands, tools, token rotation, and limitations.

Anyone with the MCP token can use the endpoint, and the curated tools can return
peer configuration and QR data. Protect it as a high-privilege credential. SSE,
OAuth2, shell access, and arbitrary filesystem tools are not provided.

## Can the application e-mail peer configurations?

Yes. Configure SMTP through environment variables; the minimum is `EMAIL_HOST`,
`EMAIL_PORT`, and `EMAIL_DEFAULT_FROM_EMAIL`. Full setup, provider examples,
and troubleshooting are in [EMAIL-SETUP.md](./EMAIL-SETUP.md).

## Does it check for updates?

The **Allow Check Updates** setting can check the GitHub releases page. When
`WG_ALLOW_CHECK_UPDATES` is supplied at startup, it overrides that database
setting; when it is absent, the database setting is used. Invalid environment
values are rejected. When enabled, the footer can show the running version and a
newer release link. No update is applied automatically; review releases and back
up before replacing the image.

## What happens during an image upgrade?

On startup the container backs up the SQLite database, runs migrations,
initializes application/MCP state, clears cache, regenerates WireGuard files,
brings up `/config/wireguard/wg0.conf` when present, and starts Django. In-place
migrations are intended to be safe, but upgrades can fail. Test new images and
keep a rollback path.

## What must I back up?

Back up both the host directory mounted at `/data` (including
`wg_ui_plus.db`) and the host directory mounted at `/config` (WireGuard config
and generated scripts) before upgrades or major changes. Protect backups because
they may contain private keys and other credentials.

## Is it safe to expose the UI to the Internet?

Not by itself. The example Compose file enables `CORS_ALLOW_ALL_ORIGINS=true`,
uses placeholder paths, and has a host UDP `1195`/default-container UDP `51820`
mapping that does not match the application's default `WG_PORT_EXTERNAL=1196`.
Restrict CORS, use strong credentials, place the UI behind a TLS reverse proxy,
limit network access, and expose only the WireGuard UDP port as needed. Read
[DEPLOYMENT.md](./DEPLOYMENT.md) before remote exposure.

## What credentials need special care?

The application password, peer private keys, QR codes, downloaded `.conf` files,
SMTP password, and MCP token are sensitive. Do not commit them, put them in
public Compose files, or include them in logs and support requests. Rotate tokens
and peer configurations if they may have been exposed.
