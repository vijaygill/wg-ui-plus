FROM python:alpine3.20

ARG UNAME=pi
ARG UID=1000
ARG GID=1000


RUN apk update && apk upgrade && apk add --no-cache --update wireguard-tools iptables openresolv net-tools iptraf-ng procps tcpdump sudo conntrack-tools
RUN pip install  --no-cache-dir  --break-system-packages --upgrade qrcode colorlog Django djangorestframework django-cors-headers django-spa drf-standardized-errors

RUN apk add --no-cache gcc libressl-dev musl-dev libffi-dev \
    &&  pip install --no-cache-dir cryptography \
    &&  apk del gcc libressl-dev musl-dev libffi-dev

RUN adduser -D $UNAME
#RUN echo "${UNAME}:pass" | chpasswd

RUN echo '%pi ALL=(ALL) NOPASSWD:ALL'>>/etc/sudoers 

RUN mkdir -p /app /clientapp /data /config && chown $UID:$GID /app /clientapp /data /config

VOLUME /app /clientapp /data /config

COPY src/clientapp/dist/wg-ui-plus/browser /clientapp
COPY src/api_project/ /app

USER $UNAME

RUN cd /app && ./manage.py migrate
ENTRYPOINT ["/app/manage.py", "runserver", "0.0.0.0:8000"]
