#!/bin/bash

WORKDIR="/Users/tonrausch/test_env/shared"

if [ -d $WORKDIR ]; then
sudo rm -r $WORKDIR/* 
fi

docker compose down
docker system prune -a
docker compose up -d 

