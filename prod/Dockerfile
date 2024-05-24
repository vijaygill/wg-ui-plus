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
        wireguard wireguard-tools python3-cryptography net-tools iproute2 iptables openresolv wireguard wireguard-tools python3-cryptography net-tools iproute2 iptables openresolv \
		&& pip install --break-system-packages --upgrade qrcode colorlog Django djangorestframework django-cors-headers django-spa drf-standardized-errors \
		&& usermod -aG sudo $UNAME && echo "$UNAME  ALL=(ALL) NOPASSWD:ALL">>/etc/sudoers \
		&& mkdir -p /app /clientapp /data /config && chown $UID:$GID /app /clientapp /data /config

VOLUME /app /clientapp /data /config

COPY src/clientapp/dist/wg-ui-plus/browser /clientapp
COPY src/api_project/ /app

USER $UNAME

RUN cd /app && ./manage.py migrate
ENTRYPOINT ["/app/manage.py", "runserver", "0.0.0.0:8000"]
