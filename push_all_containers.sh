#!/bin/bash

echo "pushing all containers..."
docker push pulltin/test_env:client_curl &&
docker push pulltin/test_env:client_aioquic &&
docker push pulltin/test_env:router_1 &&
docker push pulltin/test_env:router_2 &&
docker push pulltin/test_env:server 
