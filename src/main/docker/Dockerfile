FROM python:alpine as build

RUN apk add --no-cache npm

RUN npm install -g @angular/cli

COPY app/wg-ui-plus /src

RUN cd /src && ng build

# TODO build the python stuff, presuming there's some sort of optommisation we can do there

FROM python:alpine

# RUN apk add --no-cache conntrack
RUN apk add --no-cache conntrack-tools
RUN apk add --no-cache iproute2
RUN apk add --no-cache iptables
RUN apk add --no-cache iptraf-ng
RUN apk add --no-cache libcap2
# RUN apk add --no-cache libcap2-bin
RUN apk add --no-cache net-tools
RUN apk add --no-cache openresolv
RUN apk add --no-cache procps
# RUN apk add --no-cache python3-cryptography
RUN apk add --no-cache py-cryptography
RUN apk add --no-cache sqlite
RUN apk add --no-cache sudo
RUN apk add --no-cache tcpdump
# RUN apk add --no-cache wireguard
RUN apk add --no-cache wireguard-tools

RUN pip install --break-system-packages --upgrade \
	colorlog \
	docker \
	Flask \
	qrcode \
	sqlalchemy

COPY /app/webapp/ /app/webapp/

# This target should change at some stage
COPY --from=build /src/dist/wg-ui-plus/browser/ /app/wg-ui-plus/dist/wg-ui-plus/browser

RUN mkdir -p /app/data

# This would at some stage be volume mounted, might not be a terrible idea to create it anyway
WORKDIR /app/webapp

CMD ["python", "app.py"]
