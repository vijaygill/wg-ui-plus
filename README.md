# WireGuard UI Plus

A Dockerised UI to mange a WireGuard VPN Server, intended to be used in companion with the [LinuxServe WireGuard Docker](https://github.com/linuxserver/docker-wireguard) image.

## Features

At this early stage, this is more of an idea of what features this management will offer at some stage

* View the live status of the WG server, what clients are connected etc.
* Add/remove clients
* General management of the server
* Configure per client iptable rules - allowing limiting not only what IPs a client can reach, but what ports/protocols can be used
* Hot reload WG with config changes (ideally without impacting currently connected clients)
* User/Group management, letting people login to get their client configs (especially via QR code)

## Usage

In short, you do you.
Our recommended approach is to use Docker compose such that you have one container for the WG server itself, and another for this management tool.
The web UI is only using `HTTP`, and thus not secured; to run this securely you should use a reverse proxy to handle `HTTPS`.
If you have the reverse proxy and the management UI using the same Docker Network, then you should not need to expose the unsecured `HTTP` ports, and the reverse proxy can connect via the container name, thus saving you from worrying about what IP the Web IP is using within Docker.

## Development guide

This repository comes with a Docker based development environment, for more details, see [devenv.md](devenv.md).
