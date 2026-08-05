###############################################################################
# Unified multi-stage Dockerfile for WireGuard UI Plus
#
# Targets:
#   base-dev  – Node.js + Python (Debian), for development and Angular build
#   base-live – Python only (Alpine), for production runtime
#   builder   – Angular build stage (extends base-dev)
#   dev       – Development shell (extends base-dev)
#   live      – Production image (extends base-live, artifacts from builder)
###############################################################################

# ---------------------------------------------------------------------------
# Global build args
# ---------------------------------------------------------------------------
ARG UNAME=pi
ARG UID=1000
ARG GID=1000
ARG APP_VERSION="v0.0.0"

# ---------------------------------------------------------------------------
# Stage 1: base-dev  (Debian + Node.js + Python)
# ---------------------------------------------------------------------------
FROM node:latest AS base-dev

ARG UNAME
ARG UID
ARG GID
ARG APP_VERSION

RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python-is-python3 \
        git \
        sqlite3 wireguard wireguard-tools \
        net-tools iproute2 iptables libcap2-bin libcap2 \
        iptraf-ng procps tcpdump \
        sudo conntrack tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN npm update -g npm \
    && npm install -g @angular/cli

RUN pip install --break-system-packages --no-cache-dir --upgrade \
        qrcode[pil] colorlog "Django>=5.1,<5.2" "djangorestframework>=3.15,<3.17" django-cors-headers \
        django-spa drf-standardized-errors django-dirtyfields requests cryptography \
        django-mcp-server==0.5.6 mcp==1.9.4

ENV APP_VERSION=${APP_VERSION}
ENV IMAGE_STAGE=base-dev

RUN groupadd -g $GID -o $UNAME \
    && useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME \
    && echo "$UNAME:$UNAME" | chpasswd \
    && usermod -aG sudo $UNAME \
    && for a in $UNAME node; do echo "$a  ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers; done

# ---------------------------------------------------------------------------
# Stage 2: base-live  (Alpine + Python)
# ---------------------------------------------------------------------------
FROM python:alpine AS base-live

ARG UNAME
ARG UID
ARG GID
ARG APP_VERSION

RUN apk update \
    && apk upgrade \
    && apk add --no-cache --update \
        wireguard-tools iptables openresolv net-tools \
        iptraf-ng procps tcpdump sudo conntrack-tools \
        tzdata gcc libressl-dev musl-dev libffi-dev bind-tools \
    && pip install --no-cache-dir --break-system-packages --upgrade \
        qrcode[pil] colorlog "Django>=5.1,<5.2" "djangorestframework>=3.15,<3.17" django-cors-headers \
        django-spa drf-standardized-errors django-dirtyfields cryptography requests \
        django-mcp-server==0.5.6 mcp==1.9.4 \
    && apk del gcc libressl-dev musl-dev libffi-dev \
    && rm -rf /var/cache/apk/*

ENV APP_VERSION=${APP_VERSION}
ENV IMAGE_STAGE=base-live

RUN addgroup --gid "$GID" "$UNAME" \
    && adduser $UNAME --disabled-password --gecos "" --ingroup "$UNAME" --no-create-home --uid "$UID" \
    && echo '%pi ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# ---------------------------------------------------------------------------
# Stage 3: builder  (Angular build)
# ---------------------------------------------------------------------------
FROM base-dev AS builder

ARG UNAME
ARG UID
ARG GID
ARG APP_VERSION

RUN mkdir -p /wg-ui-plus

WORKDIR /wg-ui-plus

# Copy dependency manifests first for better layer caching
COPY src/clientapp/package.json src/clientapp/package-lock.json /wg-ui-plus/src/clientapp/

RUN cd /wg-ui-plus/src/clientapp && npm install --force

# Copy full source
COPY . /wg-ui-plus

RUN chown -R $UNAME:$UNAME /wg-ui-plus

# Build Angular
RUN cd /wg-ui-plus/src/clientapp \
    && ng build --configuration production --prerender=false --deploy-url="/" --base-href="/" --aot=true

ENV APP_VERSION=${APP_VERSION}
ENV IMAGE_STAGE=base-dev-builder

# ---------------------------------------------------------------------------
# Stage 4: dev  (Development shell)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Stage 5: live  (Production runtime)
# ---------------------------------------------------------------------------
FROM base-live AS live

ARG UNAME
ARG UID
ARG GID
ARG APP_VERSION

RUN mkdir -p /app /app/scripts /data /config

COPY --from=builder /wg-ui-plus/src/clientapp/dist/wg-ui-plus/browser /app/clientapp
COPY --from=builder /wg-ui-plus/src/api_project/ /app/api_project
COPY --from=builder /wg-ui-plus/scripts/run-app.sh /app/scripts
COPY --from=builder /wg-ui-plus/scripts/monitor-*.sh /app/scripts
COPY --from=builder /wg-ui-plus/LICENSE /app

RUN chown -R $UID:$GID /app /data /config

VOLUME /data /config
WORKDIR /app

ENV APP_VERSION=${APP_VERSION}
ENV IMAGE_STAGE=live

USER $UNAME
ENTRYPOINT [ "/app/scripts/run-app.sh" ]
