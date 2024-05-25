#!/bin/bash

cd /app/api_project
bash
./manage.py migrate
./manage.py runserver 0.0.0.0:8000
