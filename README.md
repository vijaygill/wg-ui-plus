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

## Screenshots ##
* Home page showing some Peers-Groups and Peers disabled.
  ![image](https://github.com/vijaygill/wg-ui-plus/assets/8999486/8f938e8c-a8a0-4def-acc8-868d9f4e50b6)

* Peer-Groups list page
  ![image](https://github.com/vijaygill/wg-ui-plus/assets/8999486/ed583785-3b09-401b-b5eb-84945a625b76)

* Peer-Group "LAN Users" allows only my mobile phone to access LAN (192.168.0.0/24)
  ![image](https://github.com/vijaygill/wg-ui-plus/assets/8999486/b3ac96de-dac5-445d-8d72-5f0960ba7442)

* Server Configuration page where you can generate configuration files for WireGuard and IPTables.
  ![image](https://github.com/vijaygill/wg-ui-plus/assets/8999486/567215b8-53a8-4fc6-aadb-cacab239de37)

* And finally, the Peer page where you can see the QR code to add tunnel on your client device.
  ![image](https://github.com/vijaygill/wg-ui-plus/assets/8999486/6ca7a44f-841e-42f7-acda-9d0bbae82fe7)


## Usage
Clone this repo and simply run "./run-dev-app".
It will build docker image for dev so be patient.
Once it finishes, just point your browser at the host where this application is running and it listens on port 8000. For example in my case it is "http://orangepi5-plus:8000/" (I am using an OrangePi5-plus for devlopment).
The web UI is only using `HTTP`, and thus not secured; to run this securely you should use a reverse proxy to handle `HTTPS`.

## Development guide

This repository comes with a Docker based development environment, for more details, see [devenv.md](devenv.md).
