#!/bin/bash

cd /wg-ui-plus/src/api_project
cd /app/api_project
./manage.py migrate
./manage.py runserver 0.0.0.0:8000
