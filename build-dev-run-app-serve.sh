#!/bin/bash

./build-dev.sh && docker run -it --rm -p 13080:80 -v /home/pi/temp/wg-ui-plus:/wg-ui-plus -v "./gitconfig":/home/pi/.gitconfig:ro wg-ui-plus /wg-ui-plus/scripts/run-app.sh
