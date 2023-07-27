#!/bin/bash


# set up tc qdisc program 1 on router_1 & router_2
docker exec router_1 ./netsim.sh "$@"
docker exec router_2 ./netsim.sh "$@"


# start tcpdump router_1 & router_2 
#docker exec router_1 ./start_tcpdump.sh
#docker exec router_2 ./start_tcpdump.sh


docker exec router_1 ./start_ping.sh 



# stop tcpdump router_1 & router_2
#docker exec router_1 ./stop_tcpdump.sh
#docker exec router_2 ./stop_tcpdump.sh

# rsync files with macbookair
#rsync -aP --delete $WORKDIR -e "ssh -i $PATH_SSH_PUB_KEY" $PATH_REMOTE_HOST

