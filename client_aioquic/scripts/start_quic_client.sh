#!/bin/bash

PATH_QLOG=/shared/qlog
PATH_KEYS=/shared/keys/client.key


echo "client_aioquic: sending quic request..."

rm -r /shared/ticket.txt

python /aioquic/examples/http3_client.py -k https://172.3.0.5:4433/echo --secrets-log $PATH_KEYS --quic-log $PATH_QLOG --zero-rtt --session-ticket /shared/ticket.txt &&
python /aioquic/examples/http3_client.py -k https://172.3.0.5:4433/echo --secrets-log $PATH_KEYS --quic-log $PATH_QLOG --zero-rtt --session-ticket /shared/ticket.txt 

echo "client_aioquic: quic connection closed."
