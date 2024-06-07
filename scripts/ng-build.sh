#!/bin/bash

APP_FOLDER='/wg-ui-plus/src/clientapp'
if [[ ! -d "${APP_FOLDER}" ]] ; then
	echo 'Appears to be the first run. Performing some boot strapping...'
	mkdir -p "${APP_FOLDER}"
	cd "${APP_FOLDER}"
	npm install
fi

cd "${APP_FOLDER}"

mkdir -p /wg-ui-plus/src/clientapp/dist
sudo chown -R pi:pi /wg-ui-plus/src/clientapp/dist

ng build --configuration development --watch --prerender=false --deploy-url="/" --base-href="/"
