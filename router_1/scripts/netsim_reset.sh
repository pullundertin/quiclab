#!/bin/bash

echo "router_1: initializing tc qdisc..."
tc qdisc del dev eth0 root 2>/dev/null
tc qdisc del dev eth1 root 2>/dev/null
