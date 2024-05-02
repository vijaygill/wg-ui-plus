FROM debian:latest

RUN apt-get update -y && apt-get upgrade && apt-get install -y python3-pip

RUN apt-get install -y python3 python-is-python3

RUN pip install --break-system-packages --upgrade Flask

RUN apt-get install -y npm

RUN npm install -g @angular/cli

ARG UNAME=pi
ARG UID=1000
ARG GID=1000

RUN groupadd -g $GID -o $UNAME && useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME

USER $UNAME

WORKDIR /wg-ui-plus/app


