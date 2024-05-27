# WireGuard UI Plus

A Dockerised UI to run and manage a WireGuard VPN in the same container.

## Usage
You can set up your own VPN in a few minutes by following the following steps:
1. Gather the following information
   * IP address assigned to you router (refered to as External IP address in this document )
   * IP address of the machine / raspberry pi / any other SBC you are going to use to run the VPN (refered to as Internal IP address in this document ).
2. Using the port forwarding feature of your router, forward the port 1196 to the port 51820 and use internal IP address as the target machine.
3. Now start the WG-UI-Plus using one of the following two options
    Option 1:
     * Run the following command
       ```
       mkdir ./config && mkdir ./data && docker run -it --rm --cap-add CAP_NET_ADMIN --cap-add NET_ADMIN --cap-add SYS_MODULE --sysctl net.ipv4.conf.all.src_valid_mark=1 --sysctl net.ipv4.ip_forward=1 --privileged -v "${PWD}/data":/data -v "${PWD}/config":/config -v /lib/modules:/lib/modules:ro -v /tmp:/tmp -p "1196:51820/udp" -p "8000:8000" ghcr.io/vijaygill/wg-ui-plus:dev
       ```
    Option 2:
     * Clone this repo and simply execute the following command
       ```
       "./run-app-live-from-ghcr.sh"
       ```
4. Point your browser to the address "htttp://internel_ip_address:8000".
5. In the server configuration page
   * In the server configuration page, use the external ip address for the value for the field "Host Name External". For long term setup, have a domain name set up pointing to your IP address (I use duckdns).
   ![image](https://github.com/vijaygill/wg-ui-plus/assets/8999486/d224d5f1-ec8a-4a08-9c9e-783a56fb273b)
   * Change the upstream DNS server to suitable value. I have pihole on 192.168.0.5 in my setup. you can use 8.8.8.8 also.
   * Click on "Generate Wireguard Configuration Files" and "Restart WireGuard".
6. In Peers management page, add a new Peer
   * Open the edit page for any peer and leave it open to scan QR code in next step
     ![image](https://github.com/vijaygill/wg-ui-plus/assets/8999486/2851ad9b-9bfa-4b61-9aa1-0dfbdaf9d855)


7. Install WirGuard app on your mobile phone and add tunnel by scannign the QR code.
8. You should be able to access internet on your mobile phone via the VPN.

Now you can start adding more targets and peer-groups and peers to configure the VPN in any way you need.

Note: Every Peer is member of "EveryOne" Peer-Group. In this setup, I enabled the target "Internet" for "Everyone", hence my mobile phone can access the internet also via the VPN. This could be stopped by removing the Target from EveryOne peer-group in Peer-Group edit page.

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

## Development guide

This repository comes with a Docker based development environment, for more details, see [devenv.md](devenv.md).
