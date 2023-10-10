#!/bin/bash

source .env

version=$(date +%Y%m%d_%I%M%S)

echo "creating a copy of all containers..."
docker tag pulltin/test_env:$ARCH pulltin/test_env_bak:$ARCH.$version 
docker tag pulltin/test_env:file_server pulltin/test_env_bak:file_server.$version 

echo "backing up all containers..."
docker push pulltin/test_env:$ARCH
docker push pulltin/test_env_bak:$ARCH.$version 
docker push pulltin/test_env:file_server
docker push pulltin/test_env_bak:file_server.$version 

