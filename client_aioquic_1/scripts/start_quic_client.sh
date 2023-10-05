#!/bin/bash

PATH_QLOG=/shared/qlog_client
PATH_KEYS=/shared/keys/client.key


echo "client_aioquic_1: sending quic request..."

rm -r /shared/ticket.txt

# run multiple streams
python /aioquic/examples/http3_client.py -k https://172.3.0.5:4433/echo https://172.3.0.5:4433/echo --secrets-log $PATH_KEYS --quic-log $PATH_QLOG --zero-rtt --session-ticket /shared/ticket.txt 


echo "client_aioquic_1: quic connection closed."
