#!/bin/bash

# Check argument for protocol type
if [ $1 != "quic" ]; then
    echo "$HOST: resetting tcp_probe trace..."
    if [ -e "/sys/kernel/debug/tracing/trace" ]; then
        echo "" > /sys/kernel/debug/tracing/trace
        echo "$HOST: tcp_probe trace resetted." 
    fi

    # setup tcpprobe
    echo 1 > /sys/kernel/debug/tracing/events/tcp/enable 
fi

echo "server: starting tcpdump..."
tcpdump -i eth0 -w $PCAP_PATH >> $LOG_PATH 2>&1 & 
