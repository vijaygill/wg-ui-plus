#!/bin/bash

docker build -t wg-ui-plus -f Dockerfile . && docker run -it --rm -p 13080:80 -v /home/pi/temp/wg-ui-plus:/wg-ui-plus -v "./gitconfig":/root/.gitconfig:ro wg-ui-plus bash

