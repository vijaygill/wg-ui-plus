FROM debian:latest

ARG UNAME=pi
ARG UID=1000
ARG GID=1000
ARG ARG_GID_DOCKER=999

RUN groupadd -g $GID -o $UNAME && useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME

RUN groupadd -g $ARG_GID_DOCKER -o docker && usermod -aG docker $UNAME

RUN apt-get update -y \
	&& apt-get upgrade -y \
	&& apt-get install -y \
		python3-pip \
		python3 \
		python-is-python3 \
		npm \
		sqlite3

RUN npm install -g @angular/cli

RUN pip install --break-system-packages --upgrade \
	Flask \
	sqlalchemy \
	docker

RUN apt-get install -y python3-cryptography

RUN pip install --break-system-packages --upgrade qrcode

RUN apt install -y wireguard wireguard-tools

RUN mkdir -p /app && chown $UID:$GID /app

VOLUME /app

USER $UNAME

WORKDIR /wg-ui-plus/app

