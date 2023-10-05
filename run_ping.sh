#!/bin/bash

WORKDIR=/root/test_env/shared/
PATH_SSH_PUB_KEY=/root/.ssh/mba
PATH_REMOTE_HOST="marco@mba:/Users/Marco/shared/"


# delete all files in shared folder
if [ "$(ls -A $WORKDIR/pcap/)" ]; then
	rm -r $WORKDIR/pcap/*
fi

if [ "$(ls -A $WORKDIR/qlog/)" ]; then
	rm -r $WORKDIR/qlog/*
fi

if [ "$(ls -A $WORKDIR/keys/)" ]; then
	rm -r $WORKDIR/keys/*
fi


docker exec client ./start_tcpdump.sh
docker exec router_1 ./start_tcpdump.sh
docker exec router_2 ./start_tcpdump.sh
docker exec server ./start_tcpdump.sh

# set up tc qdisc program 1 on router_1 & router_2
docker exec router_1 ./netsim.sh "$@"
docker exec router_2 ./netsim.sh "$@"



docker exec server ./start_ping.sh & 
pid=$!
wait $pid

docker exec client ./stop_tcpdump.sh
docker exec router_1 ./stop_tcpdump.sh
docker exec router_2 ./stop_tcpdump.sh
docker exec server ./stop_tcpdump.sh

# rsync files with macbookair
rsync -aP --delete $WORKDIR -e "ssh -i $PATH_SSH_PUB_KEY" $PATH_REMOTE_HOST
