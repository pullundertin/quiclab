#!/bin/bash

echo "router_2: starting tcpdump..."
tcpdump -i eth0 -w /shared/pcap/router_2_eth0.pcap 2>/dev/null &
tcpdump -i eth1 -w /shared/pcap/router_2_eth1.pcap 2>/dev/null &

