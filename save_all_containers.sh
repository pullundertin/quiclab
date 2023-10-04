#!/bin/bash

echo "commiting images..."
docker commit client_curl pulltin/test_env:client_curl &&
docker commit client_aioquic pulltin/test_env:client_aioquic &&
docker commit router_1 pulltin/test_env:router_1 &&
docker commit router_2 pulltin/test_env:router_2 &&
docker commit server pulltin/test_env:server 
