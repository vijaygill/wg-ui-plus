ARG UNAME=pi
ARG UID=1000
ARG GID=1000
ARG APP_VERSION="v0.0.0"

# Stage: base-dev
FROM debian:latest AS base-dev
ARG UNAME
ARG UID
ARG GID
ARG APP_VERSION

RUN apt-get update -y \
	&& apt-get upgrade -y \
	&& apt-get install -y \
	python3 \
	python3-pip \
	python-is-python3 \
	git \
	npm \
	sqlite3 wireguard wireguard-tools python3-cryptography \
	net-tools iproute2 iptables libcap2-bin libcap2 \
	iptraf-ng procps tcpdump \
	sudo conntrack tzdata

RUN npm install -g @angular/cli

RUN pip install --break-system-packages --upgrade qrcode colorlog Django djangorestframework django-cors-headers django-spa drf-standardized-errors django-dirtyfields requests

ENV APP_VERSION=${APP_VERSION}
ENV IMAGE_STAGE=base-dev

RUN groupadd -g $GID -o $UNAME && useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME && echo "$UNAME:$UNAME" | chpasswd
RUN usermod -aG sudo $UNAME && echo "$UNAME  ALL=(ALL) NOPASSWD:ALL">>/etc/sudoers

# Stage: builder
FROM base-dev AS builder
ARG UNAME
ARG UID
ARG GID
ARG APP_VERSION

RUN mkdir -p /wg-ui-plus

COPY . /wg-ui-plus

RUN chown -R $UNAME:$UNAME /wg-ui-plus

RUN cd /wg-ui-plus/src/clientapp && npm install --force && ng build --configuration production --prerender=false --deploy-url="/" --base-href="/"

ENV APP_VERSION=${APP_VERSION}
ENV IMAGE_STAGE=base-dev-builder

# Stage: dev
FROM base-dev AS dev
ARG UNAME
ARG UID
ARG GID
ARG APP_VERSION

RUN mkdir -p /app /data /config && chown $UID:$GID /app /data /config
VOLUME /app /data /config

ENV APP_VERSION=${APP_VERSION}
ENV IMAGE_STAGE=dev

USER $UNAME
WORKDIR /wg-ui-plus/src

# Stage: base-live
FROM python:alpine AS base-live
ARG UNAME
ARG UID
ARG GID
ARG APP_VERSION

RUN apk update && apk upgrade && apk add --no-cache --update wireguard-tools iptables openresolv net-tools iptraf-ng procps tcpdump sudo conntrack-tools tzdata

RUN apk add --no-cache --update gcc libressl-dev musl-dev libffi-dev \
	&&  pip install --no-cache-dir --break-system-packages --upgrade qrcode colorlog Django djangorestframework django-cors-headers django-spa drf-standardized-errors django-dirtyfields cryptography requests \
	&&  apk del gcc libressl-dev musl-dev libffi-dev

ENV APP_VERSION=${APP_VERSION}
ENV IMAGE_STAGE=base-live

RUN adduser -D $UNAME
RUN echo '%pi ALL=(ALL) NOPASSWD:ALL'>>/etc/sudoers
RUN mkdir -p /app /app/scripts /data /config && chown $UID:$GID /app /data /config
VOLUME /data /config

# Stage: live
FROM base-live AS live
ARG UNAME
ARG UID
ARG GID
ARG APP_VERSION
COPY --from=builder /wg-ui-plus/src/clientapp/dist/wg-ui-plus/browser /app/clientapp
COPY --from=builder /wg-ui-plus/src/api_project/ /app/api_project
COPY --from=builder /wg-ui-plus/scripts/run-app.sh /app/scripts
COPY --from=builder /wg-ui-plus/scripts/monitor-*.sh /app/scripts
COPY --from=builder /wg-ui-plus/LICENSE /app
ENV APP_VERSION=${APP_VERSION}
ENV IMAGE_STAGE=live
USER $UNAME
WORKDIR /app
ENTRYPOINT [ "/app/scripts/run-app.sh" ]

