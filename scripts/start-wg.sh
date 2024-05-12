#!/bin/bash

#ip link add dev wg0 type wireguard
#ip address add dev wg0 192.168.2.1/24
#ifconfig

sudo wg-quick down /app/wireguard/wg0.conf
sudo wg-quick up /app/wireguard/wg0.conf
while true
do
    sudo wg show
    sleep 2
    clear
done
