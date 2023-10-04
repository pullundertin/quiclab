#!/bin/bash

PATH_PCAP=/shared/pcap/client_2.pcap
echo "client_aioquic_2: starting tcpdump..."
tcpdump -i eth0 -w $PATH_PCAP 2>/dev/null& 
