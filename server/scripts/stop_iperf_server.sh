#!/bin/bash

echo "$HOST: stopping iperf server..."
pkill iperf3 >> $LOG_PATH 2>&1

