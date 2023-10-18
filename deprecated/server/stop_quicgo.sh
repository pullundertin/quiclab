#!/bin/bash

echo "$HOST: stopping quicgo server..."
sleep 3
pkill -P $(pgrep go) >> $LOG_PATH 2>&1


