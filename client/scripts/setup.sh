#!/bin/bash

# set ip routes
route add -net 172.2.0.0/24 gw 172.1.0.3 eth0
route add -net 172.3.0.0/24 gw 172.1.0.3 eth0

# disable TCP Fast Open
sysctl -w net.ipv4.tcp_fastopen=0

# set initial latency
tc qdisc add dev eth0 root handle 1: netem delay 5ms


