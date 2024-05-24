# WireGuard UI Plus

A Dockerised UI to manage a WireGuard VPN Server.

## Features

At this early stage, this is more of an idea of what features this management will offer at some stage
* Terms used in the applications and their definitions
  * Target - a host, a network or whole world of internet.
  * Peer - A device that connects to VPN
  * Peer-Group - A group of peers that can be granted / denied access to targets 
* View the live status of the WG server, what clients are connected etc.
* Add/remove clients
* General management of the server

Functionality implemented/yet to be implemented so far (getting ready for first release)
- [x] Manage targets - Add/Edit/Disable.
  - [x] Add/Remove Peer-Groups from Target's list thus allowing/denying access.
- [x] Manage Peers - Add/Edit/Disable.
  - [x] Add/Remove Peers from Peer-Groups
  - [x] Alow/Deny Targets for a given Peer-Group
- [x] Manage Peer-Groups - Add/Edit/Disable
  - [x] Add/Remove Peer-Groups from Peer's list, thus affecting the access to the target linked with the Peer-Group
- [ ] Live Dashboard


## Usage

Guide to use this application will be posted as soon as it reaches 1.0 stage.
Recommended approach is to use Docker to make deployment and upgrades easier.
The web UI is only using `HTTP`, and thus not secured; to run this securely you should use a reverse proxy to handle `HTTPS`.

## Development guide

This repository comes with a Docker based development environment, for more details, see [devenv.md](devenv.md).
