#!/bin/bash

# Get ENVIRONMENT VARIABLES
source ./.env

# Error handling
set -e

# Variable names
WORKDIR=$ROOT_DIR/test_env/shared/
SSH_PUBLIC_KEY_PATH="$ROOT_DIR/.ssh/mba"
REMOTE_HOST="marco@192.168.2.9:/Users/Marco/shared"
OUTPUT="$ROOT_DIR/test_env/shared/output.log"
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
folders=("$WORKDIR/pcap" "$WORKDIR/logs" "$WORKDIR/qlog_client" "$WORKDIR/qlog_server" "$WORKDIR/keys")
for folder in "${folders[@]}"; do
    rm -rf "$folder"/*
done

# Delete output file
[ -e "$OUTPUT" ] && rm -f "$OUTPUT"

echo -e "[$SECTION_1]" > $OUTPUT
echo -e "\n[$SECTION_2]" >> $OUTPUT
echo -e "\n[$SECTION_3]" >> $OUTPUT
echo -e "\n[$SECTION_4]" >> $OUTPUT

section_1() {
	tee >(xargs -I {} sed -i "/$SECTION_1/a {}" $OUTPUT)
}

section_2() {
	tee >(xargs -I {} sed -i "/$SECTION_3/i {}" $OUTPUT)
}

section_3() {
	tee >(xargs -I {} sed -i "/$SECTION_4/i {}" $OUTPUT)
}

section_4() {
	tee >(xargs -I {} sed -i "/$SECTION_4/a {}" $OUTPUT)
}


function help() {
      echo "Usage: netsim"
      echo -e "-c\t\tCLIENT\t\t\t\tcurl | aioquic"
      echo -e "-i\t\tFIREWALL\t\t\t0 | From:To"
      echo -e "-p\t\tPROTOCOL\t\t\thttp | https | quic | iperf"
      echo -e "-f\t\tFILE SIZE\t\t\tinteger in bytes"
      echo -e "-d\t\tDELAY\t\t\t\tinteger in ms"
      echo -e "-a\t\tDELAY DEVIATION\t\t\tinteger in ms"
      echo -e "-l\t\tLOSS\t\t\t\tinteger in %"
      echo -e "-r\t\tRATE\t\t\t\tinteger in Gbit"
      echo -e "-w\t\twindow scaling\t\t\t0/1"
      echo -e "--rmin\t\trecieve window minimum\t\tinteger in bytes"
      echo -e "--rdef\t\trecieve window default\t\tinteger in bytes"
      echo -e "--rmax\t\trecieve window maximum\t\tinteger in bytes"
      exit 1

}


#set flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        -c|--client)
            CLIENT="$2"
            shift 2
            ;;
        -i|--firewall)
            FIREWALL="$2"
            shift 2
            ;;
        -p|--protocol)
            PROTO="$2"
            shift 2
            ;;
        -f|--file-size)
            FILE_SIZE="$2"
            shift 2
            ;;
        -d|--delay)
            DELAY="$2"
            shift 2
            ;;
        -a|--delay-deviation)
            DELAY_DEVIATION="$2"
            shift 2
            ;;
        -l|--loss)
            LOSS="$2"
            shift 2
            ;;
        -r|--rate)
            RATE="$2"
            shift 2
            ;;
        -w|--window-scaling)
            WINDOW_SCALING="$2"
            shift 2
            ;;
        --rmin)
            RMIN="$2"
            shift 2
            ;;
        --rdef)
            RDEF="$2"
            shift 2
            ;;
        --rmax)
            RMAX="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
			help
            exit 1
            ;;
    esac
done



date | section_1 

# List of container names
containers=("client_aioquic_1" "client_aioquic_2" "router_1" "router_2" "server")
routers=("router_1" "router_2")
clients=("client_aioquic_1" "client_aioquic_2")

# Iterate over containers and start tcpdump
for container in "${containers[@]}"; do
    docker exec "$container" ./scripts/start_tcpdump.sh | section_2
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

# start server
docker exec server ./scripts/start_"$PROTO"_server.sh | section_2 &
sleep 3 &&

# run request
docker exec client_aioquic_1 ./scripts/start_"$PROTO"_client.sh  | section_2 

# 0-RTT !
sleep 5
docker exec client_aioquic_2 ./scripts/start_"$PROTO"_client.sh | section_2 

# stop server
sleep 3
docker exec server ./scripts/stop_"$PROTO"_server.sh | section_2


# Iterate over containers and stop tcpdump
for container in "${containers[@]}"; do
	docker exec "$container" ./scripts/stop_tcpdump.sh | section_2 &
done

sleep 3
# Rsync files with remote host
rsync -ahP --delete "$WORKDIR" -e "ssh -i $SSH_PUBLIC_KEY_PATH" "$REMOTE_HOST" >> "$OUTPUT"
