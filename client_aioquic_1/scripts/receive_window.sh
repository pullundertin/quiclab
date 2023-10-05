#!/bin/bash

WINDOW_SCALING=$(echo $1 | awk '{print $1}')
RMIN=$(echo $1 | awk '{print $2}')
RDEF=$(echo $1 | awk '{print $3}')
RMAX=$(echo $1 | awk '{print $4}')


# tcp settings
sysctl -w net.ipv4.tcp_window_scaling=$WINDOW_SCALING &>/dev/null
RMEM="$RMIN $RDEF $RMAX"
sysctl -w net.ipv4.tcp_rmem="$RMEM" &>/dev/null



echo "client_aioquic_1: window scaling=$WINDOW_SCALING, receive window=$RMEM."
