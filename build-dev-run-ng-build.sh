#!/bin/bash

BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"

source ${BASE_DIR}/build-dev.sh

docker run -it --rm -v "${BASE_DIR}":/wg-ui-plus -v "${BASE_DIR}/gitconfig":/home/pi/.gitconfig:ro -v /tmp:/tmp wg-ui-plus /wg-ui-plus/scripts/ng-build.sh
