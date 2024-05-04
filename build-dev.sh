#!/bin/bash

BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"
ARG_UNAME=$(whoami)
ARG_UID=$(id -u)
ARG_GID=$(id -g)

docker build --build-arg UNAME="${ARG_UNAME}" --build-arg UID="${ARG_UID}" --build-arg GID="${ARG_GID}" -t wg-ui-plus -f Dockerfile .
