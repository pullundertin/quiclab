#!/bin/bash


function change_ip() {
    sleep 1
    echo "$HOST: changing ip address..."
    #ip addr del 172.1.0.101/24 dev eth0 >> /shared/logs/client.log 2>&1
    #ip addr add 172.1.0.200/24 dev eth0 >> /shared/logs/client.log 2>&1
    #ip link set dev eth0 down >> /shared/logs/client.log 2>&1
    # wait

    # ip link set dev eth0 up >> /shared/logs/client.log 2>&1
    # # wait
    # # set ip routes
    # route add -net 172.2.0.0/24 gw 172.1.0.3 eth0 >> /shared/logs/client.log 2>&1
    # route add -net 172.3.0.0/24 gw 172.1.0.3 eth0 >> /shared/logs/client.log 2>&1
    # echo "$HOST: ip address changed."

}

function reset_ip() {

    echo "$HOST: resetting ip address..."

    #ip addr del 172.1.0.200/24 dev eth0
    ip addr add 172.1.0.101/24 dev eth0
    ip link set eth0 down &&
    ip link set eth0 up &&
    # set ip routes
    route add -net 172.2.0.0/24 gw 172.1.0.3 eth0 &&
    route add -net 172.3.0.0/24 gw 172.1.0.3 eth0 &&
    echo "$HOST: reset is done."
}

# reset_ip
echo "$HOST: sending quic request..."


# # run multiple streams
#python /aioquic/examples/http3_client.py -k https://172.3.0.5:4433/echo https://172.3.0.5:4433/echo --secrets-log $KEYS_PATH --quic-log $QLOG_PATH --zero-rtt --session-ticket /shared/ticket.txt 

#ip a s dev eth0
python /aioquic/examples/http3_client.py -k https://172.3.0.5:4433/echo --secrets-log $KEYS_PATH --quic-log $QLOG_PATH --zero-rtt --session-ticket $TICKET_PATH >> $LOG_PATH 2>&1 &

change_ip & 
wait  
#ip a s dev eth0

#reset_ip 
# sleep 5

# reset_ip
# #python /aioquic/examples/http3_client.py -k https://172.3.0.5:4433/echo --secrets-log $KEYS_PATH --quic-log $QLOG_PATH --zero-rtt --session-ticket /shared/ticket.txt 

# echo "$HOST: quic connection closed."

