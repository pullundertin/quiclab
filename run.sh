#!/bin/bash


WORKDIR=/root/test_env/shared/
PATH_SSH_PUB_KEY=/root/.ssh/mba
PATH_REMOTE_HOST="marco@mba:/Users/Marco/shared/"
OUTPUT=$WORKDIR/output.log
PROTO="http"
DELAY=0
DELAY_DEVIATION=0
LOSS=0
WINDOW_SCALING=1
RMIN=4096
RDEF=131072
RMAX=6291456
FILE_SIZE="1M"
FIREWALL=0
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


function help() {
      echo "Usage: netsim"
      echo "	-i		FIREWALL		0 | From:To"
      echo "	-p		PROTOCOL		http | https | quic | iperf"
      echo "	-f		FILE SIZE		integer in bytes"
      echo "    -d              DELAY			integer in ms"
      echo "    -a              DELAY DEVIATION         integer in ms"
      echo "    -l              LOSS                    integer in %"
      echo "    -r              RATE                    integer in Gbit"
      echo "    -w              window scaling          0/1"
      echo "    --rmin          recieve window minimum  integer in bytes"
      echo "    --rdef          recieve window default  integer in bytes"
      echo "    --rmax          recieve window maximum  integer in bytes"
      exit 1

}


#set flags
while getopts ":i:p:f:d:a:l:r:w:-:" option; do
	case $option in
	i)
		FIREWALL="$OPTARG"
		;;
	p)
	     	PROTO="$OPTARG"
	     	;;
	f)
		FILE_SIZE="$OPTARG"
 	    	;;
        d)
		DELAY="$OPTARG"
		;;
	a)
		DELAY_DEVIATION="$OPTARG"
		;;
	l)
		LOSS="$OPTARG"
		;;
	r)
		RATE="$OPTARG"
		;;
	w)
		WINDOW_SCALING="$OPTARG"
		;;
	-)
              	case "${OPTARG}" in
                rmin)
                    RMIN="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 ))
                    ;;
                rdef)
                    RDEF="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 ))
                    ;;
                rmax)
                    RMAX="${!OPTIND}"; OPTIND=$(( $OPTIND + 1 ))
                    ;;

                *)
		    if [ "$OPTERR" = 1 ] && [ "${optspec:0:1}" != ":" ]; then
                                echo "Unknown option --${OPTARG}" >&2
                    fi
		    help
                    ;;
      		esac
      		;;
	*)
  			if [ "$OPTERR" = 1 ] && [ "${optspec:0:1}" != ":" ]; then
                        	echo "Unknown option --${OPTARG}" >&2
                    	fi
	     	help
	     	;;										
        esac	
done


date | section_1 
docker exec client ./start_tcpdump.sh | section_2
docker exec router_1 ./start_tcpdump.sh | section_2
docker exec router_2 ./start_tcpdump.sh | section_2
docker exec server ./start_tcpdump.sh | section_2


docker exec router_1 ./netsim.sh "$DELAY $DELAY_DEVIATION $LOSS $RATE" | section_3
docker exec router_2 ./netsim.sh "$DELAY $DELAY_DEVIATION $LOSS $RATE" | section_3
docker exec client ./receive_window.sh "$WINDOW_SCALING $RMIN $RDEF $RMAX" | section_3
if [ $FIREWALL == "0" ]; then
docker exec client ./firewall_disable.sh
else 
docker exec client ./firewall_enable.sh "$FIREWALL"
sleep 2
fi

# set data size if argument not empty
if [ ! -z "$FILE_SIZE" ]; then
docker exec server ./generate_data.sh $FILE_SIZE
fi
echo "File size: $FILE_SIZE" | section_3

# start server
docker exec server ./start_"$PROTO"_server.sh | section_2 &
sleep 1 &&

# run request
docker exec client ./start_"$PROTO"_client.sh | section_2 &&

# stop server
sleep 3
docker exec server ./stop_"$PROTO"_server.sh | section_2

# reset firewall
docker exec client ./firewall_disable.sh 

docker exec client ./stop_tcpdump.sh | section_2
docker exec router_1 ./stop_tcpdump.sh | section_2
docker exec router_2 ./stop_tcpdump.sh | section_2
docker exec server ./stop_tcpdump.sh | section_2

# rsync files with macbookair
rsync -ahPvv --delete $WORKDIR  -e "ssh -i $PATH_SSH_PUB_KEY" $PATH_REMOTE_HOST >> $OUTPUT
