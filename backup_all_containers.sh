#!/bin/bash

version=$(date +%Y%m%d_%I%M%S)

echo "creating a copy of all containers..."
docker tag pulltin/test_env:client_curl pulltin/test_env_bak:client_curl.$version 
docker tag pulltin/test_env:client_aioquic pulltin/test_env_bak:client_aioquic.$version 
docker tag pulltin/test_env:router_1 pulltin/test_env_bak:router_1.$version 
docker tag pulltin/test_env:router_2 pulltin/test_env_bak:router_2.$version
docker tag pulltin/test_env:server pulltin/test_env_bak:server.$version

echo "backing up all containers..."
docker push pulltin/test_env_bak:client_curl.$version &&
docker push pulltin/test_env_bak:client_aioquic.$version &&
docker push pulltin/test_env_bak:router_1.$version &&
docker push pulltin/test_env_bak:router_2.$version &&
docker push pulltin/test_env_bak:server.$version
