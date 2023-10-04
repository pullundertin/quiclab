#!/bin/bash

PATH_PCAP=/shared/pcap/server.pcap
echo "server: starting tcpdump..."
tcpdump -i eth0 -w $PATH_PCAP 2>/dev/null& 
