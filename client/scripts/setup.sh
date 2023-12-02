#!/bin/bash

# set ip routes
route add -net 172.2.0.0/24 gw 172.1.0.3 eth0
route add -net 172.3.0.0/24 gw 172.1.0.3 eth0

# disable TCP Fast Open
sysctl -w net.ipv4.tcp_fastopen=0

# disable Forward RTO Recovery
sysctl -w net.ipv4.tcp_frto=0

# disable RACK
sysctl -w net.ipv4.tcp_recovery=4

# set initial latency
tc qdisc add dev eth0 root handle 1: netem delay 5ms

# disable rx tx checksum
ethtool --offload  eth0  rx off  tx off

# disable generic segmentation offload
ethtool -K eth0 gso off



