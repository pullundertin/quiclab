#!/bin/bash

echo "$HOST: starting quicgo server..."
cd /quic-go/example/ &&
go run main.go --qlog &
sleep 3  


