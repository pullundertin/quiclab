#!/bin/bash
# save tcpprobe to file
cat /sys/kernel/debug/tracing/trace > /shared/tcpprobe/$HOST.log
echo 0 > /sys/kernel/debug/tracing/events/tcp/enable

echo "$HOST: stopping $HOST tcpdump..."
pkill tcpdump
