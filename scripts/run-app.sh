#!/bin/bash

WG_CONF_FILE="/config/wireguard/wg0.conf"
cd /app/api_project
./manage.py makemigrations
./manage.py migrate
./manage.py db_init_db_on_start
./manage.py clear_cache
./manage.py wg_generate_config

if test -f "${WG_CONF_FILE}"
then
    sudo wg-quick up "${WG_CONF_FILE}"
fi

./manage.py runserver 0.0.0.0:8000
