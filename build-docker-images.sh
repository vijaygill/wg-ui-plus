#!/bin/bash

DEV_ONLY="no"

APP_VERSION="v0.0.0"
APP_COMMIT_ID=$(git rev-parse HEAD)

if [[ "$*" == *"dev-only"* ]]
then
    DEV_ONLY="yes"
fi

echo "DEV_ONLY = ${DEV_ONLY}"

BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"
source ${BASE_DIR}/set-script-vars.sh

docker build --target=dev --build-arg UNAME="${ARG_UNAME}" --build-arg UID="${ARG_UID}" --build-arg GID="${ARG_GID}" --build-arg ARG_GID_DOCKER="${ARG_GID_DOCKER}" --build-arg APP_VERSION="${APP_VERSION}" -t wg-ui-plus-dev -f Dockerfile .

if [ "${DEV_ONLY}" != "yes" ]
then
    docker build --target=live --build-arg UNAME="${ARG_UNAME}" --build-arg UID="${ARG_UID}" --build-arg GID="${ARG_GID}" --build-arg ARG_GID_DOCKER="${ARG_GID_DOCKER}" --build-arg APP_VERSION="${APP_VERSION}" -t wg-ui-plus-live -f Dockerfile .
fi

