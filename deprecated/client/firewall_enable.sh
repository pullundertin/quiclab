#!/bin/bash

iptables -F && 
iptables -I OUTPUT 1 -p tcp -d 172.3.0.5 -m connbytes --connbytes 200000:270000 --connbytes-dir reply --connbytes-mode bytes -j DROP  


#echo "$HOST: setting up firewall rules..."
#iptables -I INPUT 1 -p tcp -d 172.3.0.5 -m connbytes --connbytes $1 --connbytes-dir reply --connbytes-mode bytes -j DROP >> $LOG_PATH 2>&1
#iptables -I INPUT 1 -p udp -d 172.3.0.5 -m connbytes --connbytes $1 --connbytes-dir reply --connbytes-mode bytes -j DROP >> $LOG_PATH 2>&1
#iptables -I OUTPUT 1 -p tcp -d 172.3.0.5 --tcp-flags ACK ACK -m connbytes --connbytes $1 --connbytes-dir reply --connbytes-mode bytes -j DROP >> $LOG_PATH 2>&1
