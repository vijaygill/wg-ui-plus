#!/bin/bash

docker build -t wg-ui-plus -f Dockerfile . && docker run -it --rm -p 13080:80 -v ./app:/app wg-ui-plus bash

