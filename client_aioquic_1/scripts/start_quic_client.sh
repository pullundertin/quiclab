#!/bin/bash

PATH_QLOG=/shared/qlog_client
PATH_KEYS=/shared/keys/client.key


echo "client_aioquic_1: sending quic request..."

#rm -r /shared/ticket.txt

# run multiple streams
python /aioquic/examples/http3_client.py -k https://172.3.0.5:4433/echo https://172.3.0.5:4433/echo --secrets-log $PATH_KEYS --quic-log $PATH_QLOG --zero-rtt --session-ticket /shared/ticket.txt 

echo "client_aioquic_1: changing ip address..."
ip addr del 172.1.0.101/24 dev eth0
ip addr add 172.1.0.200/24 dev eth0
ip link set dev eth0 down
ip link set dev eth0 up
# set ip routes
route add -net 172.2.0.0/24 gw 172.1.0.3 eth0
route add -net 172.3.0.0/24 gw 172.1.0.3 eth0

python /aioquic/examples/http3_client.py -k https://172.3.0.5:4433/echo --secrets-log $PATH_KEYS --quic-log $PATH_QLOG --zero-rtt --session-ticket /shared/ticket.txt 

echo "client_aioquic_1: quic connection closed."

echo "client_aioquic_1: resetting ip address..."

ip addr del 172.1.0.200/24 dev eth0
ip addr add 172.1.0.101/24 dev eth0
ip link set eth0 down
ip link set eth0 up
# set ip routes
route add -net 172.2.0.0/24 gw 172.1.0.3 eth0
route add -net 172.3.0.0/24 gw 172.1.0.3 eth0