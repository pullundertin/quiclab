#!/bin/bash

# run_quic data_size program

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

# if no program has been declared (if string is zero)
if [  -z "$2" ]; then
# initialize tc qdisc on router_1 & router_2
docker exec router_1 ./tc_qdisc_default.sh
docker exec router_2 ./tc_qdisc_default.sh

else
# set up tc qdisc program 1 on router_1 & router_2
docker exec router_1 ./tc_qdisc_prog_$2.sh
docker exec router_2 ./tc_qdisc_prog_$2.sh

fi

# start tcpdump router_1 & router_2
docker exec router_1 ./start_tcpdump.sh
docker exec router_2 ./start_tcpdump.sh

# set data size if argument not empty
if [ ! -z "$1" ]; then
docker exec server ./generate_data.sh $1
fi

# start server
docker exec server ./start_https_server.sh 

# run request
docker exec client ./start_https_client.sh &&

# stop server
sleep 3
docker exec server ./stop_https_server.sh
docker exec client ./stop_tcpdump.sh

# stop tcpdump router_1 & router_2
docker exec router_1 ./stop_tcpdump.sh
docker exec router_2 ./stop_tcpdump.sh

# rsync files with macbookair
rsync -aP --delete $WORKDIR -e "ssh -i $PATH_SSH_PUB_KEY" $PATH_REMOTE_HOST

