#!/bin/bash

while true
do
    sudo iptables -n -L -v --line-numbers
    sleep 3
    clear
done
