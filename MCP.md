# MCP server

MCP support is disabled by default. Set `MCP_SERVER_ENABLED=true` (or `1`,
`yes`, `y`, `on`) to enable it at startup. `false`, `0`, `no`, `n`, and `off`
disable it. Any other value is rejected. When the variable is absent, the
database setting on the **MCP Server** tab controls availability.

The Streamable HTTP endpoint is `/mcp` and requires a token header validated
against the application-managed token. Use the `Bearer` scheme when configuring
Open WebUI (this is its native Streamable HTTP MCP authentication format):

```text
Authorization: Bearer <token>
```

The legacy DRF-compatible form remains supported for existing clients:

```text
Authorization: Token <token>
```

Use the administration page to enable MCP, copy the masked token through the
authenticated copy action, or rotate it. The management commands are:

```bash
python manage.py mcp_enable
python manage.py mcp_disable
python manage.py mcp_generate_token
```

`mcp_enable` prints a token only when one did not already exist. Rotation
invalidates the previous token. The startup command creates a missing token
when MCP is enabled, but never logs the token. An explicit
`MCP_SERVER_ENABLED` value overrides database changes on startup, and commands
warn when that is possible.

The curated tools cover peer, peer-group, target, relationship, server
configuration, WireGuard configuration/generation/restart, connected peers,
status, IPTables log, hierarchy, license/application information, peer
configuration/QR retrieval, and peer configuration email. General peer tools
do not return private keys, configurations, or QR data; those are available
only from dedicated tools. No shell or arbitrary filesystem tools are exposed.

SSE and OAuth2 transports are intentionally deferred. The current transport
uses a `TokenAuthentication`-compatible application authenticator, accepts both
`Bearer` and `Token`, and permits any authenticated application user. The
browser copy operation is authenticated and returns the raw token for clipboard
use; ordinary configuration responses remain masked.

The backend images install `django-mcp-server==0.5.6` with the compatible
`mcp==1.9.4` SDK. The existing application dependencies are still installed
from package names in the Dockerfile rather than from a complete lock file, so
only the MCP integration dependency set is pinned here; a broader project
lockfile remains future work.
