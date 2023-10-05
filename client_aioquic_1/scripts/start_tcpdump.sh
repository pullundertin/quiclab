#!/bin/bash

PATH_PCAP=/shared/pcap/client.pcap
echo "client_aioquic: starting tcpdump..."
tcpdump -i eth0 -w $PATH_PCAP 2>/dev/null& 
