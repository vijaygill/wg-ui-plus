FROM python:alpine3.20

ARG UNAME=pi
ARG UID=1000
ARG GID=1000
ARG ARG_GID_DOCKER=999

RUN addgroup --gid $GID $UNAME && adduser --uid $UID -G $UNAME -D --shell /bin/bash $UNAME

RUN apk update && apk upgrade && apk add --no-cache --update wireguard-tools iptables openresolv net-tools iptraf-ng procps tcpdump sudo conntrack-tools
RUN pip install  --no-cache-dir  --break-system-packages --upgrade qrcode colorlog Django djangorestframework django-cors-headers django-spa drf-standardized-errors

RUN apk add --no-cache gcc libressl-dev musl-dev libffi-dev \
    &&  pip install --no-cache-dir cryptography \
    &&  apk del gcc libressl-dev musl-dev libffi-dev

RUN echo '%wheel ALL=(ALL) ALL' > /etc/sudoers.d/wheel
RUN adduser $UNAME wheel

RUN mkdir -p /app /clientapp /data /config && chown $UID:$GID /app /clientapp /data /config

VOLUME /app /clientapp /data /config

COPY src/clientapp/dist/wg-ui-plus/browser /clientapp
COPY src/api_project/ /app

USER $UNAME

RUN cd /app && ./manage.py migrate
ENTRYPOINT ["/app/manage.py", "runserver", "0.0.0.0:8000"]
