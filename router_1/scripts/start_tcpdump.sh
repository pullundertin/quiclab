#!/bin/bash

echo "router_1: starting tcpdump..."
tshark -i eth0 -w /shared/pcap/router_1_eth0.pcap 2>/dev/null &
tshark -i eth1 -w /shared/pcap/router_1_eth1.pcap 2>/dev/null &

