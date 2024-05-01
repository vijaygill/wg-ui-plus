#!/bin/bash

docker build -t wg-ui-plus -f Dockerfile . && docker run -it --rm -p 13080:80 -v ./app:/app -v "${HOME}/.gitconfig":/root/.gitconfig:ro  wg-ui-plus bash

