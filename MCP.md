# MCP server

MCP (Model Context Protocol) lets an MCP client manage WireGuard UI Plus
through the Streamable HTTP endpoint `/mcp`. It is disabled by default.

## Enable MCP

On the **MCP Server** tab, enable MCP and generate a token. The token is
masked in the UI; use **Copy to Clipboard** to copy the authenticated token,
or rotate it to invalidate the previous token.

To configure MCP without the database setting, set `WG_MCP_SERVER_ENABLED` to
`true` (or `1`, `yes`, `y`, `on`) or `false` (or `0`, `no`, `n`, `off`). Any
other value is rejected. When it is absent, the database setting controls
whether MCP is enabled. When it is present, it overrides that setting and the
UI control is disabled.

## Authentication

Send the generated token in the authorization header. `Bearer` is the
recommended scheme for clients such as Open WebUI; the legacy `Token` scheme
is also supported:

```text
Authorization: Bearer <token>
```

## Security

Treat the MCP token as a high-privilege credential. Anyone who possesses it
can use the MCP endpoint, including operations that expose peer configuration
or QR data. Protect the endpoint and never share or commit the token.
