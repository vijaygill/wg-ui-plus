#!/bin/bash

BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"

source ${BASE_DIR}/build-docker-images.sh


docker run -it --rm \
    --cap-add CAP_NET_ADMIN \
    --cap-add NET_ADMIN \
    --cap-add SYS_MODULE \
    --cap-add=NET_ADMIN \
    --cap-add=SYS_MODULE \
    --privileged \
    --sysctl net.ipv4.conf.all.src_valid_mark=1 \
    --sysctl net.ipv4.ip_forward=1 \
    -v "${BASE_DIR}":/wg-ui-plus \
    -v "${BASE_DIR}/src":/app \
    -v "${BASE_DIR}/src/clientapp/dist/wg-ui-plus/browser":/clientapp \
    -v "${BASE_DIR}/data":/data \
    -v "${BASE_DIR}/config":/config \
    -v "${HOME}/.gitconfig":/home/pi/.gitconfig:ro \
    -v "${BASE_DIR}/temp/vscode":/home/pi/.vscode-oss \
    -v /lib/modules:/lib/modules:ro \
    -v /tmp:/tmp \
    wg-ui-plus-dev bash

