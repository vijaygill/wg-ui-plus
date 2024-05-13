FROM python:alpine as build

RUN apk add --no-cache npm

RUN npm install -g @angular/cli

COPY app/wg-ui-plus /src

RUN cd /src && ng build

# TODO build the python stuff, presuming there's some sort of optommisation we can do there

FROM python:alpine

RUN apk add --no-cache sqlite

RUN pip install --break-system-packages --upgrade \
	Flask \
	sqlalchemy \
	docker

# COPY python server code
COPY --from=build /src/dist/wg-ui-plus/browser/ /static-ui