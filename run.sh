#!/bin/bash

# Variable names
WORKDIR=./shared/
TICKET_PATH=./shared/keys/ticket.txt
SSH_PUBLIC_KEY_PATH="../.ssh/mba"
REMOTE_HOST="marco@192.168.2.9:/Users/Marco/shared"
OUTPUT="./shared/logs/output.log"
PROTO="http"
DELAY=0
DELAY_DEVIATION=0
LOSS=0
WINDOW_SCALING=1
RMIN=4096
RDEF=131072
RMAX=6291456
FILE_SIZE="1M"
CLIENT="curl"
FIREWALL=0
SECTION_1="LOG"
SECTION_2="SEQUENCE"
SECTION_3="SETTINGS"
SECTION_4="RSYNC"


# Delete files
folders=("$WORKDIR/pcap" "$WORKDIR/logs" "$WORKDIR/qlog_client" "$WORKDIR/qlog_server" "$WORKDIR/keys" "$WORKDIR/tcpprobe")
for folder in "${folders[@]}"; do
    rm -rf "$folder"/*
done

# Set Logger up
source log.sh
setup_log

# Evaluate command options
source options.sh
set_options $@

# List of container names
containers=("client_1" "client_2" "router_1" "router_2" "server")
routers=("router_1" "router_2")
clients=("client_1" "client_2")
peers=("server" "client_1" "client_2")

# Iterate over containers and start tcpdump
for container in "${containers[@]}"; do
    docker exec "$container" ./scripts/start_tcpdump.sh $PROTO | section_2 &
done

# Iterate over routers and set netsim parameters
for router in "${routers[@]}"; do
    docker exec "$router" ./scripts/netsim.sh "$DELAY $DELAY_DEVIATION $LOSS $RATE" | section_3
done

# Iterate over clients and set tcp parameters
for client in "${clients[@]}"; do
    docker exec "$client" ./scripts/receive_window.sh "$WINDOW_SCALING $RMIN $RDEF $RMAX" | section_3
done

# set data size if argument not empty
if [ ! -z "$FILE_SIZE" ]; then
docker exec server ./scripts/generate_data.sh $FILE_SIZE
fi
echo "File size: $FILE_SIZE" | section_3

# set firewall rules
if [ $FIREWALL != "0" ]; then
    # Iterate over clients and set firewall
    for client in "${clients[@]}"; do
        docker exec "$client" ./scripts/firewall_enable.sh "$FIREWALL"
        sleep 2
    done
fi

# Iterate over peers and start communication
for peer in "${peers[@]}"; do
    docker exec "$peer" ./scripts/start_"$PROTO".sh | section_2 
done


# stop server
sleep 3
docker exec server ./scripts/stop_"$PROTO".sh | section_2


# Iterate over clients and reset firewall
for client in "${clients[@]}"; do
    docker exec "$client" ./scripts/firewall_disable.sh 
done

# Iterate over containers and stop tcpdump
for container in "${containers[@]}"; do
	docker exec "$container" ./scripts/stop_tcpdump.sh $PROTO | section_2 &
done

wait

# Rsync files with remote host
rsync -ahP --delete "$WORKDIR" -e "ssh -i $SSH_PUBLIC_KEY_PATH" "$REMOTE_HOST" >> "$OUTPUT"
