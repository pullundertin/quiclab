#!/bin/bash

route add -net $SUBNET_1 gw $GW_1 $IFACE 
route add -net $SUBNET_2 gw $GW_2 $IFACE 

