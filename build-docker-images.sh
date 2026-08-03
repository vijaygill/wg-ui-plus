#!/bin/bash

APP_VERSION="v0.0.0"

BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"
source ${BASE_DIR}/set-script-vars.sh

DOCKERFILE="${BASE_DIR}/Dockerfile"

echo "Building all Docker image targets (dev, live)."

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

build_target "dev"

build_target "live"
