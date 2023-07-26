#!/bin/bash

echo "pushing all containers..."
docker push pulltin/test_env:client &&
docker push pulltin/test_env:router_1 &&
docker push pulltin/test_env:router_2 &&
docker push pulltin/test_env:server &&
echo "upload to dockerhub completed."
