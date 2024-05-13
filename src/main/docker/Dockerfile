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


COPY /app/app.py /app/app.py

# This target should change at some stage
COPY --from=build /src/dist/wg-ui-plus/browser/ /app/wg-ui-plus/dist/wg-ui-plus/browser

RUN mkdir -p /app/data

# This would at some stage be volume mounted, might not be a terrible idea to create it anyway
WORKDIR /app

CMD ["python", "app.py"]
