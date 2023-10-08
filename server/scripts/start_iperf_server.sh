#!/bin/bash


echo "$HOST: starting iperf server..."
iperf3 -s >> $LOG_PATH 2>&1


