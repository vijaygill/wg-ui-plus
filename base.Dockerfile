ARG UNAME=pi
ARG UID=1000
ARG GID=1000
ARG APP_VERSION="v0.0.0"

# Stage: base-dev
FROM python:latest AS base-dev
ARG UNAME
ARG UID
ARG GID
ARG APP_VERSION

RUN apt-get update -y \
	&& apt-get upgrade -y \
	&& apt-get install -y \
	git \
	npm \
	sqlite3 wireguard wireguard-tools \
	net-tools iproute2 iptables libcap2-bin libcap2 \
	iptraf-ng procps tcpdump \
	sudo conntrack tzdata \
    && apt-get clean

RUN npm install -g @angular/cli

RUN pip install --break-system-packages --upgrade qrcode[pil] colorlog Django djangorestframework django-cors-headers django-spa drf-standardized-errors django-dirtyfields requests cryptography

ENV APP_VERSION=${APP_VERSION}
ENV IMAGE_STAGE=base-dev

RUN groupadd -g $GID -o $UNAME && useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME && echo "$UNAME:$UNAME" | chpasswd
RUN usermod -aG sudo $UNAME && echo "$UNAME  ALL=(ALL) NOPASSWD:ALL">>/etc/sudoers

# Stage: base-live
FROM python:alpine AS base-live
ARG UNAME
ARG UID
ARG GID
ARG APP_VERSION

RUN apk update \
    && apk upgrade

RUN apk add --no-cache --update wireguard-tools iptables openresolv net-tools \
                                iptraf-ng procps tcpdump sudo conntrack-tools \
                                tzdata gcc libressl-dev musl-dev libffi-dev \
                                bind-tools \
    &&  pip install --no-cache-dir --break-system-packages --upgrade qrcode[pil] colorlog \
                    Django djangorestframework django-cors-headers django-spa drf-standardized-errors django-dirtyfields \
                    cryptography requests \
	&&  apk del gcc libressl-dev musl-dev libffi-dev

ENV APP_VERSION=${APP_VERSION}
ENV IMAGE_STAGE=base-live

RUN addgroup --gid "$GID" "$UNAME"
RUN adduser $UNAME --disabled-password --gecos "" --ingroup "$UNAME" --no-create-home --uid "$UID"
RUN echo '%pi ALL=(ALL) NOPASSWD:ALL'>>/etc/sudoers


