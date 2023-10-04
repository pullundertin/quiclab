#!/bin/bash

iptables -I OUTPUT 1 -p tcp -d 172.3.0.5 --tcp-flags ACK ACK -m connbytes --connbytes $1 --connbytes-dir reply --connbytes-mode bytes -j DROP
