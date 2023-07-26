#!/bin/bash

# run_quic data_size program

# if no program has been declared (if string is zero)
if [  -z "$2" ]; then
# initialize tc qdisc on router_1 & router_2
docker exec router_1 tc_qdisc_default
docker exec router_2 tc_qdisc_default

else
# set up tc qdisc program 1 on router_1 & router_2
docker exec router_1 tc_qdisc_prog_$2
docker exec router_2 tc_qdisc_prog_$2

fi

# start tcpdump router_1 & router_2
docker exec router_1 start_tcpdump
docker exec router_2 start_tcpdump

# set data size if argument not empty
if [ ! -z "$1" ]; then
docker exec server ./generate_data.sh $1
fi

# start server
docker exec server start_http_server 

# run request
docker exec client start_https_client

# stop server
wait
docker exec server stop_http_server

# stop tcpdump router_1 & router_2
docker exec router_1 stop_tcpdump
docker exec router_2 stop_tcpdump

# rsync files with macbookair
rsync -aP --delete /root/test_env/shared/ -e "ssh -i /home/rspp2/.ssh/mba" marco@mba:/Users/Marco/shared/


