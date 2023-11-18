#!/bin/bash

# setup tcpprobe
mount -t debugfs none /sys/kernel/debug
echo 1 > /sys/kernel/debug/tracing/events/tcp/enable

# set ip routes
route add -net 172.1.0.0/24 gw 172.3.0.4 eth0
route add -net 172.2.0.0/24 gw 172.3.0.4 eth0
ip route change 172.1.0.0/24 via 172.3.0.4 dev eth0 initcwnd 1
sysctl -w net.ipv4.tcp_congestion_control=reno

