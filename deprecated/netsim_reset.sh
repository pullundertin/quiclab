#!/bin/bash

echo "$HOST: initializing tc qdisc..."
tc qdisc del dev eth0 root >> $LOG_PATH 2>&1
tc qdisc del dev eth1 root >> $LOG_PATH 2>&1

