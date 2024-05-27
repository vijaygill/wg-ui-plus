#!/bin/bash

BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"

source ${BASE_DIR}/set-script-vars.sh
source ${BASE_DIR}/build-docker-images.sh dev-only

DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -v \"${BASE_DIR}\":/wg-ui-plus "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -v \"${BASE_DIR}/src/api_project/\":/app/api_project "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -v \"${BASE_DIR}/src/clientapp/dist/wg-ui-plus/browser\":/app/clientapp "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -v \"${BASE_DIR}/scripts\":/app/scripts "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -v \"${HOME}/.gitconfig\":/home/pi/.gitconfig:ro "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -p \"1196:51820/udp\" "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -p \"8000:8000\" "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} --name wg-ui-dev-app "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} wg-ui-plus-dev /wg-ui-plus/scripts/run-app.sh "

eval ${DOCKER_RUN_CMD}
