#!/bin/bash

echo "$HOST: starting tcpdump..."
tcpdump -i eth0 -w $PCAP_PATH_1 >> $LOG_PATH 2>&1 &
tcpdump -i eth1 -w $PCAP_PATH_2 >> $LOG_PATH 2>&1 &

