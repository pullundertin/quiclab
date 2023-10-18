#!/bin/bash

echo "$HOST: sending quicgo request..."

cd /quic-go/example/client &&
go run main.go --keylog $KEYS_PATH --qlog --insecure https://172.3.0.6:6121/demo/tiles &



