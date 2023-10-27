#!/bin/bash

route add -net $SUBNET_1 gw $GW_1 $IFACE >> $LOG_PATH 2>&1
route add -net $SUBNET_2 gw $GW_2 $IFACE >> $LOG_PATH 2>&1

