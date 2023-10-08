#!/bin/bash
WINDOW_SCALING=$(echo $1 | awk '{print $1}')
RMIN=$(echo $1 | awk '{print $2}')
RDEF=$(echo $1 | awk '{print $3}')
RMAX=$(echo $1 | awk '{print $4}')


# tcp settings
sysctl -w net.ipv4.tcp_window_scaling=$WINDOW_SCALING >> $LOG_PATH 2>&1
RMEM="$RMIN $RDEF $RMAX"
sysctl -w net.ipv4.tcp_rmem="$RMEM" >> $LOG_PATH 2>&1



echo "$HOST: window scaling=$WINDOW_SCALING, receive window=$RMEM."
