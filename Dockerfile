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
		sqlite3 wireguard wireguard-tools python3-cryptography net-tools iproute2 iptables openresolv libcap2-bin libcap2 iptraf-ng procps tcpdump sudo conntrack

RUN npm install -g @angular/cli

# Don't forget to update CI scripts
# Can we maybe extract this list of packages out to a file so we only have to change in one place?
RUN pip install --break-system-packages --upgrade \
	docker \
	pytest \
	pytest-cov \
	sqlalchemy qrcode colorlog Django djangorestframework django-cors-headers django-spa drf-standardized-errors

RUN usermod -aG sudo $UNAME && echo "$UNAME  ALL=(ALL) NOPASSWD:ALL">>/etc/sudoers

RUN echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

RUN mkdir -p /app /clientapp /data /config && chown $UID:$GID /app /clientapp /data /config

VOLUME /app /clientapp /data /config

USER $UNAME

WORKDIR /wg-ui-plus/src

