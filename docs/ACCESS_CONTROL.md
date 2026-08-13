# Access control

WireGuard UI Plus separates a client's WireGuard identity from the resources it
can use. The canonical terms are:

- **Peer** — a client device and its WireGuard identity (keys and VPN address).
- **Peer group** — a collection of peers.
- **Target** — a resource reachable through the VPN: a host, selected ports on a
  host, or a network.

Access is granted by associating targets with peer groups. For server-side
generated access rules, a peer receives the access of every **enabled** peer group
to which it belongs, and only **enabled** targets associated with those groups are
included. Disabled peers, peer groups, and targets are excluded from those
generated access rules. Strict client `AllowedIPs` routes can retain addresses
from disabled relationships, so disabling an object should be followed by
**Apply Changes** and, when applicable, distribution of an updated peer
configuration. There is no direct peer-to-target association.

## The access model

The normal relationship is:

```text
Peer -> Peer group -> Target
```

For example, putting `Alice's laptop` in an enabled `NAS Users` group and
associating an enabled `NAS Shares` target with `NAS Users` grants Alice access to
that target. Removing either relationship, or disabling either object, removes
the resulting access after changes are applied.

`EveryOne` is a built-in special case during configuration generation: its
default targets are intended for all peers. Treat those targets as global
defaults, not as a substitute for reviewing each peer's least-privilege group
memberships. The built-in `Internet` target is initially associated with
`EveryOne`, so remove that association when full-tunnel Internet access is not
intended.

The built-in `EveryOne` peer group and its `Internet` target are created during
initialization. `EveryOne` is handled as a special global default during
configuration generation, so its targets can apply to all peers even when a
peer's editable group memberships do not show an explicit `EveryOne` entry.
Remove the `Internet` association if it is not appropriate for your deployment.

## Peers

Open **Manage Data** → **Peers** to add or edit a peer. A peer has a name,
description, optional e-mail address, a server-assigned VPN IP address, and one or
more peer groups. The application creates the WireGuard key pair and assigns an
available address from the server's **Network Address**. The IP address shown in
the editor is informational and is not manually edited there.

Use **Disabled** to block the peer's permitted traffic after configuration is
regenerated. The peer may still have configuration generated, so fully disabling
a peer requires removing its configuration from client devices.
A peer's configuration can be displayed as a QR code, downloaded with **Download
.conf file**, or sent with **Send Config By Email** when SMTP is configured (see
[EMAIL-SETUP.md](./EMAIL-SETUP.md)).

The peer's group memberships determine the targets it can access. Assign only the
groups needed by that client; membership in multiple groups combines their
access.

## Peer groups

Open **Manage Data** → **Peer-Groups** to create a logical role such as `NAS
Users`, `Administrators`, or `Guests`. Select the group's peers and targets in the
editor. Peers in a group have access to that group's selected targets.

Disabling a peer group denies its server-side access rules while preserving the
relationships for later use. Some built-in groups and targets restrict which fields can be changed;
the UI identifies those restrictions. A disabled peer group is not a substitute
for removing unnecessary memberships when designing least-privilege access.

## Targets

Open **Manage Data** → **Targets** and enter a resource in **IP
Address/Network**. Supported forms are:

- Host: `192.168.0.51`
- Network: `192.168.0.0/24`
- Selected ports on a host: `192.168.0.51:139,445`

Associate the enabled target with one or more enabled peer groups. The editor describes this as
“Selected Peer-Groups will have access to this Target.” A target can be disabled
without deleting its relationships. The built-in `Internet` target uses
`0.0.0.0/0`; configure **Local Networks** on **Server Configuration** if local
networks must not be included in that broad route.

## Worked example: Samba on a NAS

To allow one client to reach only Samba on `192.168.0.51`:

1. In **Manage Data** → **Peer-Groups**, create `NAS Shares Users`.
2. In **Manage Data** → **Peers**, create `Test NAS User` and select `NAS Shares Users`.
3. In **Manage Data** → **Targets**, create `NAS Shares` with
   `192.168.0.51:139,445` and select `NAS Shares Users`.
4. Open **VPN Layout** under **Server** and verify the peer → peer group → target
   relationships.
5. Select **Apply Changes** when the application prompts you, then open the peer
   and scan its QR code or download its `.conf` file.

The client can then use the specified Samba ports, but does not gain access to
other ports on that host merely because it is a member of the group.

## Access-Control Screenshots

The peer-group editor connects selected peers to the targets they should be able

![Peer-group editor for selecting peers and targets](../images/example-add-peergroup.PNG)

Use this screen to define a role-based collection such as the NAS users in the
worked example.

The peer editor assigns an individual client to one or more peer groups.

![Peer editor for assigning a client to peer groups](../images/example-add-peer.PNG)

These memberships determine which enabled targets the client can access through
the associated groups.

The target editor defines the host, network, or selected service ports reachable
through the VPN.

![Target editor for defining a reachable host, network, or service](../images/example-add-target.PNG)

Use a narrow host-and-port target when the client needs only a specific service.

VPN Layout provides a visual check of the resulting peer-to-group-to-target
relationships.

![VPN Layout showing peer, peer-group, and target relationships](../images/example-vpn-layout.PNG)

Review this layout after changing relationships and before applying significant
access changes.

## AllowedIPs and routing

WireGuard's `AllowedIPs` controls which destination addresses a client sends into
the VPN. Without strict mode, the client configuration routes all IPv4 traffic
through the VPN. The server-side rules still determine which targets the peer is
permitted to reach.

Enable **Strict AllowedIPs in Peer Config** in **Server Configuration** to narrow
peer routes to calculated target addresses. The client configuration can fall
back to `0.0.0.0/0` when no route is calculated. Every change to a peer group's
target relationships can require distributing an updated configuration to each
affected peer. A network target can naturally cover more addresses than a host
target.

## Applying changes

Edits are saved to the application database first. When configuration-affecting
changes are detected, use **Apply Changes** (or the restart action in **Server
Configuration**) to regenerate WireGuard files, update the related iptables
rules, and restart the VPN configuration. The client must receive a new
configuration when its keys, server endpoint, VPN address, or strict
`AllowedIPs` change.

Use **VPN Layout** before applying a significant access change. After applying,
check **Monitor Peers** and **Monitor IP-Tables**.

## Least-privilege guidance

- Create groups by role or need, not one universal group for every user.
- Prefer a host-and-port target over a whole network when one service is enough.
- Remove the `Internet` association from `EveryOne` if full-tunnel Internet access
  is not intended.
- Keep administrative and guest peers in separate groups.
- Disable or remove stale peers and groups promptly.
- Review **VPN Layout** after each relationship change and keep a record of why a
  target is assigned.
- Treat generated `.conf` files, QR codes, and private keys as credentials.
