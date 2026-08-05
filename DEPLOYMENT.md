# Deployment

WireGuard UI Plus runs the Angular web UI and Django REST API together in a
Docker container. It also manages WireGuard and generated iptables rules, so the
container needs networking privileges and persistent storage.

## Requirements and quick deployment

Install Docker on the host and ensure the host can run a container with
`NET_ADMIN`, `SYS_MODULE`, the required IPv4 sysctls, and access to the host
kernel modules. A minimal deployment is:

```bash
mkdir -p ./config ./data
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

Ensure that `./config` and `./data` are writable by the container runtime user.
By default, the application listens on UDP `51820` inside the container and TCP
`8000` for the web UI. If `WG_PORT_INTERNAL` is changed, update the container
side of the Docker port mapping (for example, `-p 1196:<new-port>/udp`). The
Docker host port and router forwarding normally remain unchanged; update them
only if you also choose to change the host or router-facing port.
`WG_PORT_EXTERNAL` remains the router-facing port written into peer endpoints.
The published image uses UID/GID `1000`; custom images may use different IDs,
in which case the bind-mounted directories must be writable by those IDs.

The container-local `/tmp` tmpfs provides temporary working space without
exposing the host's `/tmp` to the container. The `docker run` example makes it
non-persistent and applies `nosuid`, `nodev`, and `noexec`. The Compose example
also keeps `/tmp` container-local, but its current `tmpfs: /tmp` declaration does
not specify those options; add equivalent tmpfs options if that hardening is
required. A host `/tmp` bind mount is broader and should only be used when a
specific local development integration requires it.

## Docker Compose

Use [docker-compose-example.yml](./docker-compose-example.yml) as a starting
point, not as a production-ready configuration. Change the host paths, external
host name, local networks, DNS server, and other environment values.

The example maps host UDP `1195` to container UDP `51820` and host TCP `8880` to
container TCP `8000`. It currently does not set `WG_PORT_EXTERNAL`, whose
application default is `1196`. This mismatch can produce peer configurations and
router instructions for the wrong port. Either add `WG_PORT_EXTERNAL=1195` to
`environment:` or change the mapping to `1196:51820/udp`.

The example also sets `CORS_ALLOW_ALL_ORIGINS=true` for convenience. Remove it
unless required, or replace it with a specific `CORS_ALLOWED_ORIGINS` list.

## Persistent storage and privileges

Persist both directories:

- `/data` contains the SQLite database at `/data/wg_ui_plus.db`.
- `/config` contains `/config/wireguard/wg0.conf` and generated scripts.

The container uses `NET_ADMIN` and `SYS_MODULE`, mounts `/lib/modules` read-only,
and sets `net.ipv4.conf.all.src_valid_mark=1` and
`net.ipv4.ip_forward=1`. These are powerful host-level permissions. Do not
replace secure directory ownership with world-writable permissions on a
security-sensitive host.

`PUID` and `PGID` in the example Compose file are not runtime settings consumed
by the application. Custom container IDs require rebuilding with Dockerfile
arguments and changing directory ownership accordingly.

## Deployment environment

The most relevant settings are:

| Variable | Purpose and default |
| --- | --- |
| `WG_NETWORK_ADDRESS` | VPN network; default `192.168.2.0/24`. |
| `WG_HOST_NAME_EXTERNAL` | Public IP or DNS name used by peers. |
| `WG_LOCAL_NETWORKS` | Comma-separated local networks, for example `192.168.0.0/24`. |
| `WG_UPSTREAM_DNS_SERVER` | DNS server supplied to peers. |
| `WG_PORT_EXTERNAL` | Router-facing external UDP port written into peer endpoints; default `1196`. |
| `WG_PORT_INTERNAL` | Container WireGuard port; default `51820`; changing it requires updating the container-side port mapping and related forwarding configuration. |
| `WG_STRICT_ALLOWED_IPS_IN_PEER_CONFIG` | When true, generated configs use narrower relationship-based routes where calculated, with required VPN/peer routes and a possible `0.0.0.0/0` fallback. |
| `TZ` | Application time zone; default `UTC`. |
| `DJANGO_LOG_LEVEL` | Log level; default `WARN`. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed origins. Prefer this to allow-all CORS. |
| `CORS_ALLOW_ALL_ORIGINS` | Allows requests from any origin when set to a recognized true value; avoid it for exposed deployments. |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted origins for CSRF protection. |
| `SECURE_REFERRER_POLICY` | Referrer-Policy; default `same-origin`. |
| `MCP_SERVER_ENABLED` | Explicitly enables or disables MCP at startup; see [MCP.md](./MCP.md). |
| `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_PORT` | SMTP settings for sending peer configurations. |
| `EMAIL_USE_SSL` or `EMAIL_USE_TLS` | SMTP transport security; configure the mode required by the provider. |

Values supplied through the environment can override corresponding UI settings
at startup. In particular, an explicit `MCP_SERVER_ENABLED` value takes
precedence over the database setting. `WG_STRICT_ALLOWED_IPS_IN_PEER_CONFIG` is
special: startup evaluates it every time, and when it is absent the value is
treated as false, which can reset a database/UI value. Set it explicitly when
that setting must persist in an unattended deployment. Never put SMTP passwords
or MCP tokens in public files or source control.

## Initial configuration

The default login is `admin` / `admin`. Change it immediately in **Server
Configuration** → **Change Password**. Set **Host Name External**, **Upstream DNS
Server**, **Local Networks**, and the external/internal ports in **Server
Configuration**, then select **Apply Changes**. Configure peers and access using
[ACCESS_CONTROL.md](./ACCESS_CONTROL.md).

![Server Configuration screen for setting the external host, ports, DNS, and local networks](./images/wg-ui-plus-server-config.png)

![Apply Changes control for regenerating and applying the WireGuard configuration](./images/wg-ui-plus-apply-changes.png)

## Secure remote exposure

Do not expose the Django development server or the UI directly to the Internet
without controls. Put the web UI behind a reverse proxy with HTTPS, restrict
origins and firewall access, and use strong application credentials. The WireGuard
UDP port must be reachable from the clients, but the administrative TCP UI does
not need to be publicly reachable. Treat peer private keys, QR codes, downloaded
`.conf` files, and the MCP token as high-value credentials.

## Startup and upgrades

Container startup backs up the SQLite database, runs Django migrations,
initializes application and MCP state, clears cache, regenerates the WireGuard
configuration, brings up `/config/wireguard/wg0.conf` when present, and starts
Django on `0.0.0.0:8000`. In-place migrations are intended to be safe, but an
upgrade can still fail; test new images where possible.

Before upgrading, back up the host directories mapped to both `/data` and
`/config`. Keep the database backup and generated WireGuard configuration until
the new image has been verified. Startup may mutate the database and regenerate
network configuration, so use disposable mounts for tests.
