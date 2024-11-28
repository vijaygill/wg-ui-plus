#!/bin/bash

BUILD_TYPE="dev"
TARGET="dev"

APP_VERSION="v0.0.0"
APP_COMMIT_ID=$(git rev-parse HEAD)

if [[ "$*" == *"dev-only"* ]]
then
    BUILD_TYPE="dev"
fi
if [[ "$*" == *"live-only"* ]] || [[ "$*" == *"all"* ]]
then
    BUILD_TYPE="live"
fi

echo "BUILD_TYPE = ${BUILD_TYPE}"

if [ "${BUILD_TYPE}" == "dev" ]
then
    TARGET="dev"
fi
if [ "${BUILD_TYPE}" == "all" ] || [ "${BUILD_TYPE}" == "live" ]
then
    TARGET="live"
fi


BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"
source ${BASE_DIR}/set-script-vars.sh

DOCKER_BUILDKIT=1 docker build --target=${TARGET} --build-arg UNAME="${ARG_UNAME}" --build-arg UID="${ARG_UID}" --build-arg GID="${ARG_GID}" --build-arg ARG_GID_DOCKER="${ARG_GID_DOCKER}" --build-arg APP_VERSION="${APP_VERSION}" --tag "wg-ui-plus-${TARGET}" -f Dockerfile .


