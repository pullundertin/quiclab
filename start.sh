#!/bin/bash

WORKDIR="/root/test_env/shared"

if [ -d $WORKDIR ]; then
rm -r $WORKDIR/* 
fi

docker compose down
docker system prune -a
docker compose up -d 

