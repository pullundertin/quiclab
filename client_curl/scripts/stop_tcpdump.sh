#!/bin/bash

# save tcpprobe to file
cat /sys/kernel/debug/tracing/trace > /shared/tcpprobe/client.log
echo 0 > /sys/kernel/debug/tracing/events/tcp/enable

echo "client_curl: stopping client tcpdump..."
pkill tcpdump



