#!/bin/bash

PATH_QLOG=/shared/qlog_server
PATH_KEYS=/shared/keys/server.key


echo "server: starting quic server..."
python /aioquic/examples/http3_server.py --certificate /aioquic/tests/ssl_cert.pem --private-key /aioquic/tests/ssl_key.pem --secrets-log $PATH_KEYS --quic-log $PATH_QLOG --verbose >> /shared/logs/server.log 2>&1 &  


