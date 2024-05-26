#!/bin/bash

BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"

source ${BASE_DIR}/build-dev

docker run -it --rm \
  -v "${BASE_DIR}":/wg-ui-plus \
  -v "${BASE_DIR}/src":/app \
  -v "${BASE_DIR}/src/clientapp/dist/wg-ui-plus/browser":/clientapp \
  -v "${BASE_DIR}/data":/data \
  -v "${BASE_DIR}/config":/config \
  -v "${HOME}/.gitconfig":/home/pi/.gitconfig:ro \
  -v /tmp:/tmp \
  --name wg-ui-dev-ng \
  wg-ui-plus-dev /wg-ui-plus/scripts/ng-build.sh
