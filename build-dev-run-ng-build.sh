#!/bin/bash

./build-dev.sh && docker run -it --rm -v /home/pi/temp/wg-ui-plus:/wg-ui-plus -v "./gitconfig":/home/pi/.gitconfig:ro wg-ui-plus /wg-ui-plus/scripts/ng-build.sh
