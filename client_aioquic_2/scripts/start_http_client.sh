#!/bin/bash

echo "client: sending http request..."
curl http://172.3.0.5/data.log -k --output /dev/null
echo "client: http connection closed."
