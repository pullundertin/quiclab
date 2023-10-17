#!/bin/bash

echo "$HOST: stopping quic server..."
sleep 3
pkill python >> $LOG_PATH 2>&1


