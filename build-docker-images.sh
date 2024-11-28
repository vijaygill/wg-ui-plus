#!/bin/bash

BUILD_TYPE="dev"

APP_VERSION="v0.0.0"
APP_COMMIT_ID=$(git rev-parse HEAD)

if [[ "$*" == *"dev-only"* ]]
then
    BUILD_TYPE="dev"
fi
if [[ "$*" == *"live-only"* ]]
then
    BUILD_TYPE="live"
fi

echo "BUILD_TYPE = ${BUILD_TYPE}"

BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"
source ${BASE_DIR}/set-script-vars.sh

if [ "${BUILD_TYPE}" == "all" ] || [ "${BUILD_TYPE}" == "dev" ]
then
    docker build --target=dev --build-arg UNAME="${ARG_UNAME}" --build-arg UID="${ARG_UID}" --build-arg GID="${ARG_GID}" --build-arg ARG_GID_DOCKER="${ARG_GID_DOCKER}" --build-arg APP_VERSION="${APP_VERSION}" -t wg-ui-plus-dev -f Dockerfile .
fi

if [ "${BUILD_TYPE}" == "all" ] || [ "${BUILD_TYPE}" == "live" ]
then
    docker build --target=live --build-arg UNAME="${ARG_UNAME}" --build-arg UID="${ARG_UID}" --build-arg GID="${ARG_GID}" --build-arg ARG_GID_DOCKER="${ARG_GID_DOCKER}" --build-arg APP_VERSION="${APP_VERSION}" -t wg-ui-plus-live -f Dockerfile .
fi

