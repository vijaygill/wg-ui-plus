#!/bin/bash

APP_FOLDER='/wg-ui-plus/app/wg-ui-plus'
if [[ ! -d "${APP_FOLDER}" ]] ; then
	echo 'Appears to be the first run. Performing some boot strapping...'
	mkdir -p "${APP_FOLDER}"
	cd "${APP_FOLDER}"
	npm install
fi

cd "${APP_FOLDER}"
ng build --watch --prerender=false # --verbose --ssr
