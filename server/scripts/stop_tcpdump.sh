#!/bin/bash

# Check argument for protocol type
if [ $1 != "quic" ]; then
    echo "$HOST: saving tcp_probe trace to file..."
    # save tcpprobe to file
    cat /sys/kernel/debug/tracing/trace > /shared/tcpprobe/server.log &&
    python /scripts/converter.py &&
    echo 0 > /sys/kernel/debug/tracing/events/tcp/enable 
fi

echo "$HOST: stopping server tcpdump..."
pkill tcpdump >> $LOG_PATH 2>&1


