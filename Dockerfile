ARG UNAME=pi
ARG UID=1000
ARG GID=1000
ARG ARG_GID_DOCKER=999

FROM debian:latest as base-dev
ARG UNAME
ARG UID
ARG GID

RUN groupadd -g $GID -o $UNAME && useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME

RUN apt-get update -y \
	&& apt-get upgrade -y \
	&& apt-get install -y \
		python3 \
		python3-pip \
		python-is-python3 \
        git \
		npm \
		sqlite3 wireguard wireguard-tools python3-cryptography net-tools iproute2 iptables openresolv libcap2-bin libcap2 iptraf-ng procps tcpdump sudo conntrack tzdata

RUN npm install -g @angular/cli

RUN pip install --break-system-packages --upgrade qrcode colorlog Django djangorestframework django-cors-headers django-spa drf-standardized-errors django-dirtyfields

RUN usermod -aG sudo $UNAME && echo "$UNAME  ALL=(ALL) NOPASSWD:ALL">>/etc/sudoers

FROM base-dev as builder

RUN mkdir -p /wg-ui-plus

COPY . /wg-ui-plus

RUN chown -R $UNAME:$UNAME /wg-ui-plus

RUN cd /wg-ui-plus/src/clientapp && npm install --force && ng build --configuration production --prerender=false --deploy-url="/" --base-href="/"

FROM base-dev as dev

RUN mkdir -p /app /data /config && chown $UID:$GID /app /data /config
VOLUME /app /data /config
USER $UNAME
WORKDIR /wg-ui-plus/src

FROM python:alpine3.20 as base-live
ARG UNAME
ARG UID
ARG GID

RUN apk update && apk upgrade && apk add --no-cache --update wireguard-tools iptables openresolv net-tools iptraf-ng procps tcpdump sudo conntrack-tools tzdata
RUN pip install  --no-cache-dir  --break-system-packages --upgrade qrcode colorlog Django djangorestframework django-cors-headers django-spa drf-standardized-errors django-dirtyfields

RUN apk add --no-cache gcc libressl-dev musl-dev libffi-dev \
    &&  pip install --no-cache-dir cryptography \
    &&  apk del gcc libressl-dev musl-dev libffi-dev

RUN adduser -D $UNAME
RUN echo '%pi ALL=(ALL) NOPASSWD:ALL'>>/etc/sudoers
RUN mkdir -p /app /app/scripts /data /config && chown $UID:$GID /app /data /config
VOLUME /data /config

FROM base-live as live
COPY --from=builder /wg-ui-plus/src/clientapp/dist/wg-ui-plus/browser /app/clientapp
COPY --from=builder /wg-ui-plus/src/api_project/ /app/api_project
COPY --from=builder /wg-ui-plus/scripts/run-app.sh /app/scripts
COPY --from=builder /wg-ui-plus/scripts/monitor-*.sh /app/scripts
COPY --from=builder /wg-ui-plus/LICENSE /app
USER $UNAME
WORKDIR /app
ENTRYPOINT [ "/app/scripts/run-app.sh" ]

