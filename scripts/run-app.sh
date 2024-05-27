#!/bin/bash

WG_CONF_FILE="/config/wireguard/wg0.conf"
if test -f "${WG_CONF_FILE}"
then
    sudo wg-quick up "${WG_CONF_FILE}"
fi
cd /app/api_project
./manage.py migrate
./manage.py runserver 0.0.0.0:8000
