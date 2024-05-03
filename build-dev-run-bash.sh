#!/bin/bash

./build-dev.sh && docker run -it --rm -v /home/pi/temp/wg-ui-plus:/wg-ui-plus -v "./gitconfig":/home/pi/.gitconfig:ro -v /tmp:/tmp -v /var/run/docker.sock:/var/run/docker.sock wg-ui-plus bash
