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

# Don't forget to update CI scripts
# Can we maybe extract this list of packages out to a file so we only have to change in one place?
RUN pip install --break-system-packages --upgrade \
	docker \
	Flask \
	pytest \
	pytest-cov \
	sqlalchemy

RUN apt-get install -y python3-cryptography

RUN pip install --break-system-packages --upgrade qrcode

RUN apt install -y wireguard wireguard-tools

RUN apt install -y net-tools iproute2 iptables openresolv

RUN apt install -y libcap2-bin libcap2

RUN apt install -y iptraf-ng

RUN apt install -y procps 
RUN apt install -y tcpdump
RUN apt install -y sudo
RUN apt install -y conntrack

RUN usermod -aG sudo $UNAME && echo "$UNAME  ALL=(ALL) NOPASSWD:ALL">>/etc/sudoers

RUN echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

RUN mkdir -p /app && chown $UID:$GID /app

VOLUME /app

USER $UNAME

WORKDIR /wg-ui-plus/app

