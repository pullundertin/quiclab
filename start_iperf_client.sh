#!/bin/bash

echo "client: iperf client started..."
iperf3 -c 172.3.0.5 &> /dev/null
