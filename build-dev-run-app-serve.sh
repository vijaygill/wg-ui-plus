#!/bin/bash

BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"

source ${BASE_DIR}/build-dev.sh

docker run -it --rm -p 13080:80 -v "${BASE_DIR}":/wg-ui-plus -v "${BASE_DIR}/gitconfig":/home/pi/.gitconfig:ro -v /tmp:/tmp -v /var/run/docker.sock:/var/run/docker.sock wg-ui-plus /wg-ui-plus/scripts/run-app.sh
