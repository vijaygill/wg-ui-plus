#!/bin/bash

BUILD_TYPE="${1}"

APP_VERSION="v0.0.0"

case "${BUILD_TYPE}" in
    dev|live|all)
        ;;
    *)
        echo "Usage: $0 [dev|live|all]"
        exit 1
        ;;
esac

echo "BUILD_TYPE = ${BUILD_TYPE}"

BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"
source ${BASE_DIR}/set-script-vars.sh

DOCKERFILE="${BASE_DIR}/Dockerfile"

build_target() {
    local TARGET=$1
    echo "--- Building target: ${TARGET} ---"
    DOCKER_BUILDKIT=1 docker build \
        --target=${TARGET} \
        --build-arg UNAME="${ARG_UNAME}" \
        --build-arg UID="${ARG_UID}" \
        --build-arg GID="${ARG_GID}" \
        --build-arg APP_VERSION="${APP_VERSION}" \
        --tag "wg-ui-plus-${TARGET}" \
        -f "${DOCKERFILE}" .
}

if [ "${BUILD_TYPE}" == "dev" ] || [ "${BUILD_TYPE}" == "all" ]; then
    build_target "dev"
fi

if [ "${BUILD_TYPE}" == "live" ] || [ "${BUILD_TYPE}" == "all" ]; then
    build_target "live"
fi
