#!/bin/bash

if [ "${GITHUB_TOKEN}" == "" ]
then
    echo "GITHUB_TOKEN not set."
else
    IMAGE_TAG="wg-ui-plus-gh-actions"
    docker build --build-arg GITHUB_TOKEN="${GITHUB_TOKEN}" -t "${IMAGE_TAG}" -f Dockerfile .
    docker run -it --rm --env GITHUB_TOKEN="${GITHUB_TOKEN}" --env GH_TOKEN="${GITHUB_TOKEN}" -v "${PWD}":/app:ro -v /var/run/docker.sock:/var/run/docker.sock ${IMAGE_TAG} bash
fi

