ARG UNAME=pi
ARG UID=1000
ARG GID=1000
ARG APP_VERSION="v0.0.0"
ARG APP_ARCH=arm64

# Stage: base-dev
FROM ghcr.io/vijaygill/wg-ui-plus:base-dev-${APP_ARCH} AS base-dev
ARG UNAME
ARG UID
ARG GID
ARG APP_VERSION
ARG APP_ARCH

# Stage: builder
FROM base-dev AS builder
ARG UNAME
ARG UID
ARG GID
ARG APP_VERSION

RUN mkdir -p /wg-ui-plus

COPY . /wg-ui-plus

RUN chown -R $UNAME:$UNAME /wg-ui-plus

RUN cd /wg-ui-plus/src/clientapp && npm install --force && ng build --configuration production --prerender=false --deploy-url="/" --base-href="/" --aot=true

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
FROM ghcr.io/vijaygill/wg-ui-plus:base-live-${APP_ARCH} AS base-live
ARG UNAME
ARG UID
ARG GID
ARG APP_VERSION

# Stage: live
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

