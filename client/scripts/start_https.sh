#!/bin/bash

echo "$HOST: sending https request..."
SSLKEYLOGFILE=$KEYS_PATH curl https://172.3.0.5:443/data.log -k --output /dev/null >> $LOG_PATH 2>&1
echo "$HOST: https connection closed."
