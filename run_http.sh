#!/bin/bash


WORKDIR=/root/test_env/shared/
PATH_SSH_PUB_KEY=/root/.ssh/mba
PATH_REMOTE_HOST="marco@mba:/Users/Marco/shared/"
OUTPUT=$WORKDIR/output.log
FILE_SIZE="1M"
SECTION_1="LOG"
SECTION_2="SEQUENCE"
SECTION_3="SETTINGS"
SECTION_4="RSYNC"

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

if [ -e "$OUTPUT" ]; then
rm -r $OUTPUT
fi

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





#set flags
while getopts ":d:a:l:r:w:f:-:" option; do
	case $option in
	  f)
	     FILE_SIZE="$OPTARG"
 	     ;;
	   *)
	     ;;										
        esac	
done
date | section_1 
docker exec client ./start_tcpdump.sh | section_2
docker exec router_1 ./start_tcpdump.sh | section_2
docker exec router_2 ./start_tcpdump.sh | section_2
docker exec server ./start_tcpdump.sh | section_2

docker exec router_1 ./netsim.sh "$@" | section_3
docker exec router_2 ./netsim.sh "$@" | section_3
docker exec client ./receive_window.sh "$@" | section_3

# set data size if argument not empty
if [ ! -z "$FILE_SIZE" ]; then
docker exec server ./generate_data.sh $FILE_SIZE
fi
echo "File size: $FILE_SIZE" | section_3

# start server
docker exec server ./start_http_server.sh | section_2

# run request
docker exec client ./start_http_client.sh | section_2 &&

# stop server
sleep 3
docker exec server ./stop_http_server.sh | section_2


docker exec client ./stop_tcpdump.sh | section_2
docker exec router_1 ./stop_tcpdump.sh | section_2
docker exec router_2 ./stop_tcpdump.sh | section_2
docker exec server ./stop_tcpdump.sh | section_2

# rsync files with macbookair
rsync -ahPvv --delete $WORKDIR  -e "ssh -i $PATH_SSH_PUB_KEY" $PATH_REMOTE_HOST >> $OUTPUT
