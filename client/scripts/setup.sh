#!/bin/bash

# set ip routes
route add -net 172.2.0.0/24 gw 172.1.0.3 eth0
route add -net 172.3.0.0/24 gw 172.1.0.3 eth0

while [ 1 ]
do
        sleep 1
done
