#!/bin/bash

version=$(date +%Y%m%d_%I%M%S)

echo "creating a copy of all containers..."
docker tag pulltin/test_env:amd64 pulltin/test_env_bak:amd64.$version 

echo "backing up all containers..."
docker push pulltin/test_env:amd64
docker push pulltin/test_env_bak:amd64.$version 

