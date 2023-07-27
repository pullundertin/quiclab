#!/bin/bash

echo "commiting images..."
docker commit client pulltin/test_env:client &&
docker commit router_1 pulltin/test_env:router_1 &&
docker commit router_2 pulltin/test_env:router_2 &&
docker commit server pulltin/test_env:server &&
