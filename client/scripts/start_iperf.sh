#!/bin/bash

echo "$HOST: iperf client started..."
iperf3 -R -c 172.3.0.5 >> $LOG_PATH 2>&1
