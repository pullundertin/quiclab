#!/bin/bash

echo "$HOST: sending http request..."
curl http://172.3.0.5/data.log -k --output /dev/null >> $LOG_PATH 2>&1
echo "$HOST: http connection closed."
