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
		sqlite3 \
	&& rm -rf /var/lib/apt/lists/*

RUN npm install -g @angular/cli

# Don't forget to update CI scripts
# Can we maybe extract this list of packages out to a file so we only have to change in one place?
RUN pip install --break-system-packages --upgrade \
	Flask \
	sqlalchemy \
	docker

USER $UNAME

WORKDIR /wg-ui-plus/app

