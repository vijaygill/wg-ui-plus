#!/bin/bash

BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"
ARG_UNAME=$(whoami)
ARG_UID=$(id -u)
ARG_GID=$(id -g)
ARG_GID_DOCKER=$(getent group docker | cut -d ":" -f3)

docker build --build-arg UNAME="${ARG_UNAME}" --build-arg UID="${ARG_UID}" --build-arg GID="${ARG_GID}" --build-arg ARG_GID_DOCKER="${ARG_GID_DOCKER}" -t wg-ui-plus -f Dockerfile .