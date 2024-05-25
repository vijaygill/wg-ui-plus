#!/bin/bash

BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"
source ${BASE_DIR}/set-script-vars.sh

docker build --target=dev --build-arg UNAME="${ARG_UNAME}" --build-arg UID="${ARG_UID}" --build-arg GID="${ARG_GID}" --build-arg ARG_GID_DOCKER="${ARG_GID_DOCKER}" -t wg-ui-plus-dev -f Dockerfile .

docker build --target=live --build-arg UNAME="${ARG_UNAME}" --build-arg UID="${ARG_UID}" --build-arg GID="${ARG_GID}" --build-arg ARG_GID_DOCKER="${ARG_GID_DOCKER}" -t wg-ui-plus-live -f Dockerfile .

