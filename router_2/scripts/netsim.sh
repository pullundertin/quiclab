#!/bin/bash

IFACE=eth0
DELAY=$(echo $1 | awk '{print $1}')
DELAY_DEVIATION=$(echo $1 | awk '{print $2}')
LOSS=$(echo $1 | awk '{print $3}')
RATE=$(echo $1 | awk '{print $4}')

# reset netem and tbf settings
tc qdisc del dev $IFACE root 2>/dev/null

# netem settings
tc qdisc add dev $IFACE root handle 1: netem delay $DELAY $DELAY_DEVIATION loss $LOSS

# tbf settings
if [ ! -z $RATE ]; then
RATE=$(echo $RATE \* 1000000000 | bc)
BURST=$(echo "$RATE/2" | bc)
LIMIT=$(echo "$RATE + $BURST/2" | bc)

tc qdisc add dev $IFACE parent 1: handle 2: tbf rate $RATE burst $BURST limit $LIMIT
fi

# print results	
STATUS_NETEM=$(tc qdisc show dev $IFACE root | awk -F "1000 " '{print $2}')
STATUS_TBF=$(tc qdisc show dev $IFACE | awk -F "rate|burst" '{print $2}')
echo "router_2: $STATUS_NETEM, $STATUS_TBF."
