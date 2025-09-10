#!/bin/bash

BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"

source ${BASE_DIR}/set-script-vars.sh
#source ${BASE_DIR}/build-docker-images.sh

DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -p \"1196:51820/udp\" "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -p \"8000:8000\" "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} --hostname wg-ui-dev-app-ghcr --name wg-ui-dev-app-ghcr ghcr.io/vijaygill/wg-ui-plus:master"

eval ${DOCKER_RUN_CMD}

