# Email setup

The application can send a peer's current WireGuard configuration by SMTP. SMTP
configuration is supplied through environment variables when the container
starts; it is not entered in the peer form.

## Bare-minimum local Postfix relay

For an unauthenticated local Postfix relay, only three environment variables
are required — `EMAIL_HOST`, `EMAIL_PORT`, and `EMAIL_DEFAULT_FROM_EMAIL`. No
username, password, TLS, or SSL settings are needed.

For example, the following values were tested against a Postfix relay running
on a NAS (they are the values used in `set-script-vars.sh`):

```text
EMAIL_HOST=cm3588-nas-01.gillsoft.home
EMAIL_PORT=9025
EMAIL_DEFAULT_FROM_EMAIL=pi@cm3588-nas-01.gillsoft.home
```

## Setting the SMTP environment variables

The minimum configuration requires `EMAIL_HOST`, `EMAIL_PORT`, and
`EMAIL_DEFAULT_FROM_EMAIL`. Username and password are optional, but must be
supplied together when used. TLS and SSL are optional and default to false;
they cannot both be enabled.

Boolean values are case-insensitive and may be written as `true`, `1`, `yes`,
or `on`, or as `false`, `0`, `no`, or `off`. TLS and SSL must not both be
enabled.

Authenticated Gmail/app-password SMTP remains supported. For Gmail only
`EMAIL_USE_TLS` is needed; `EMAIL_USE_SSL` can be omitted because it defaults
to false:

```text
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-account@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_DEFAULT_FROM_EMAIL=your-account@gmail.com
```

## Why are `EMAIL_USE_TLS` and `EMAIL_USE_SSL` needed?

`EMAIL_USE_TLS` and `EMAIL_USE_SSL` are mutually exclusive SMTP security
settings (following the conventions used by Django and similar frameworks) that
define how the application secures its SMTP connection. Never set both to
`True`.

- `EMAIL_USE_TLS=True` uses **explicit encryption**: the connection starts as
  plain text and is upgraded to encrypted communication using the STARTTLS
  command. This is the modern standard for services such as Gmail, Outlook, and
  most corporate mail servers, and normally uses port `587`.
- `EMAIL_USE_SSL=True` uses **implicit encryption**: the entire communication
  channel is wrapped in an SSL/TLS security wrapper from the very first byte.
  This is used by legacy or specific secure server setups that require an
  implicit secure tunnel from the start, and normally uses port `465`.

| Setting | Recommended port | Connection type |
| --- | --- | --- |
| `EMAIL_USE_TLS=True`, `EMAIL_USE_SSL=False` | `587` | Explicit (STARTTLS) |
| `EMAIL_USE_TLS=False`, `EMAIL_USE_SSL=True` | `465` | Implicit (SSL) |

Both settings default to `false` when unset, which is correct for an
unauthenticated local Postfix relay such as the bare-minimum example above.

## Passing the values to Docker

Prefer a protected env file for SMTP credentials. Create `./email.env` with the
placeholder values below, make the file readable only by the account that needs
it, and exclude it from source control (for example, use `chmod 600
./email.env`):

```text
EMAIL_HOST=mail.local
EMAIL_PORT=25
EMAIL_USE_TLS=False
EMAIL_USE_SSL=False
EMAIL_DEFAULT_FROM_EMAIL=wg-ui-plus@mail.local
```

For a one-off `docker run`, add `--env-file ./email.env` to the **full Quick
Start `docker run` command** in [README.md](../README.md); the SMTP-only example
below is complete and retains the required WireGuard capabilities, mounts,
ports, and tmpfs:

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
examples or for a controlled test. The checked-in `docker-compose-example.yml`
contains placeholders only.

## Restart or recreate the container

Environment variables are read by the running process at startup. For Compose,
recreate the service after changing them, for example `docker compose up -d
--force-recreate wireguard`. A plain `docker restart` does not replace the
environment stored in an existing container. For `docker run`, stop and remove
the old container and create it again with the updated `--env-file`.

## Test SMTP from the server configuration page

Open **Server Configuration** and select **Send Test Email**. The authenticated
action sends a simple message from `EMAIL_DEFAULT_FROM_EMAIL` to that same
address; it never accepts an arbitrary test recipient and includes no peer or
QR data.

## Save the recipient on the peer

In the web UI, open the peer, enter its e-mail address, and save the peer. The
send action uses only this saved database address. It does not accept an
alternate recipient address in the button action or request, so verify the
address before sending.

## Send the configuration

With SMTP configured and a saved peer address, open the peer and select **Send
Config By Email**. Confirm the action. At send time the server generates the
current `.conf` and QR image and attaches both to the message; it does not use a
configuration or QR attachment supplied by the caller.

## Verify delivery

A successful action means the SMTP backend accepted the message for sending. It
does not prove that the message reached the final inbox. Check the recipient's
spam/quarantine folders and the provider's mail logs as well as the application
notification.

## Email troubleshooting

- If the button is unavailable, read the displayed SMTP status explanation and
  check that all required variables are present in the container, that their
  names are exact, and that the container was recreated after they changed.
- An invalid port, boolean value, sender address, partial username/password
  pair, or combination of TLS and SSL causes the SMTP configuration to be
  rejected. Use a numeric port, accepted boolean forms, and supply credentials
  together.
- For Gmail authentication failures, confirm that two-step verification is
  enabled and that `EMAIL_HOST_PASSWORD` is an app password. Confirm the
  account username and sender address are valid, and that the container can
  reach `smtp.gmail.com:587`.
- Confirm the peer's saved e-mail address is valid. The server will not send to
  an address supplied separately from the peer record.
- If SMTP accepts the message but it is not visible, inspect spam/quarantine
  and provider delivery logs. A provider may accept a message and later defer
  or reject it; application success alone cannot establish inbox delivery.
- Review container logs for the provider's connection or authentication error,
  but redact passwords, app passwords, tokens, and message contents before
  sharing logs.
