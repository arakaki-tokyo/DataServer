#!/bin/bash

if [ ! $1 ]; then
	NAME=f1
else
	NAME=$1
fi

CMD='bash' # debug

docker run -dit --name $NAME \
	-e APP_PATH='/srv' \
	-e CALL='datasrv:create_app' \
	-v $PWD/mnt:/srv \
	myflask $CMD