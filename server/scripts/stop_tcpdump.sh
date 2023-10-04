#!/bin/bash

# save tcpprobe to file
cat /sys/kernel/debug/tracing/trace > /shared/tcpprobe/server.log
echo 0 > /sys/kernel/debug/tracing/events/tcp/enable

echo "server: stopping server tcpdump..."
pkill tcpdump


