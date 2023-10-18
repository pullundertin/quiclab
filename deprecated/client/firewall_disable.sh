#!/bin/bash

echo "$HOST: flushing iptables..."
iptables --flush >> $LOG_PATH 2>&1
