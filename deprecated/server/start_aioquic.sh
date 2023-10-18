#!/bin/bash

echo "$HOST: starting quic server..."
python /aioquic/examples/http3_server.py --certificate /aioquic/tests/ssl_cert.pem --private-key /aioquic/tests/ssl_key.pem --quic-log $QLOG_PATH --verbose >> $LOG_PATH 2>&1 & 
sleep 3  


