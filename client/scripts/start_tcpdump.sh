#!/bin/bash

echo "$HOST: starting tcpdump..."
tcpdump -i eth0 -w $PCAP_PATH >> $LOG_PATH 2>&1 
