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

#set flags
while getopts ":d:a:l:r:w:f:-:" option; do
	case $option in
	  f)
	     FILE_SIZE="$OPTARG"
 	     ;;
	   *)
	     ;;														               esac														  done

docker exec client ./start_tcpdump.sh
docker exec router_1 ./start_tcpdump.sh
docker exec router_2 ./start_tcpdump.sh
docker exec server ./start_tcpdump.sh

docker exec router_1 ./netsim.sh "$@"
docker exec router_2 ./netsim.sh "$@"
docker exec client ./receive_window.sh "$@"

# set data size if argument not empty
if [ ! -z "$FILE_SIZE" ]; then
docker exec server ./generate_data.sh $FILE_SIZE
fi

# start server
docker exec server ./start_http_server.sh 

# run request
docker exec client ./start_http_client.sh &&

# stop server
sleep 3
docker exec server ./stop_http_server.sh


docker exec client ./stop_tcpdump.sh
docker exec router_1 ./stop_tcpdump.sh
docker exec router_2 ./stop_tcpdump.sh
docker exec server ./stop_tcpdump.sh

# rsync files with macbookair
rsync -aP --delete $WORKDIR -e "ssh -i $PATH_SSH_PUB_KEY" $PATH_REMOTE_HOST

