#!/bin/bash

if [ ! $1 ]; then
	NAME=f1
else
	NAME=$1
fi

CMD='cd $APP_PATH && FLASK_APP=datasrv FLASK_ENV=development flask run -h 0.0.0.0 -p 80' # debug

docker run -dit --name $NAME \
	-e APP_PATH='/srv' \
	-e CALL='datasrv:create_app' \
	-v $PWD/mnt:/srv \
	myflask bash -c "${CMD}"