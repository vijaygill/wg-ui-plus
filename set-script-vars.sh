#!/bin/bash
BASE_DIR="$(dirname "$(readlink -f "${BASH_SOURCE}")")"

DOCKER_ENV_FILE="${BASE_DIR}/docker-env.txt"

ARG_UNAME=$(whoami)
ARG_UID=$(id -u)
ARG_GID=$(id -g)
APP_VERSION="dev-$(git rev-parse HEAD)"

DOCKER_RUN_CMD=""
DOCKER_RUN_CMD="${DOCKER_RUN_CMD}docker run -it --rm "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} --env-file \"${DOCKER_ENV_FILE}\""
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -e APP_VERSION=${APP_VERSION}"
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} --cap-add CAP_NET_ADMIN "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} --cap-add NET_ADMIN "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} --cap-add SYS_MODULE "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} --cap-add=NET_ADMIN "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} --cap-add=SYS_MODULE "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} --sysctl net.ipv4.conf.all.src_valid_mark=1 "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} --sysctl net.ipv4.ip_forward=1 "
#DOCKER_RUN_CMD="${DOCKER_RUN_CMD} --sysctl net.ipv4.ping_group_range='0   2147483647' "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} --privileged "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -v \"${BASE_DIR}/data\":/data "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -v \"${BASE_DIR}/config\":/config "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -v /lib/modules:/lib/modules:ro "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -v /tmp:/tmp "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -v /etc/localtime:/etc/localtime:ro "
DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -v /etc/timezone:/etc/timezone:ro "

env | grep "^WG_" > /tmp/env.txt
while read -r line
do
    DOCKER_RUN_CMD="${DOCKER_RUN_CMD} -e ${line}"
done < /tmp/env.txt
