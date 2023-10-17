#!/bin/bash

# Update ubuntu
apt update && 
apt upgrade -y &&

# Install dependencies
apt install git vim python-is-python3 pip curl iputils-ping net-tools bc iproute2 libssl-dev python3-dev nginx tcpdump iptables -y &&

# Install quic-go
git clone https://github.com/quic-go/quic-go.git



