#!/bin/bash
PATH_QLOG=/shared/qlog_client
PATH_KEYS=/shared/keys/client.key


echo "client_curl: sending quic request..."

# multiple Connections
#QLOGDIR=$PATH_QLOG SSLKEYLOGFILE=$PATH_KEYS curl --http3 https://172.3.0.5:4433/echo -k --output /dev/null && QLOGDIR=$PATH_QLOG SSLKEYLOGFILE=/shared/keys/client_2.key curl --http3 https://172.3.0.5:4433/echo -k --output /dev/null

# multiple Connections on several Ports
#QLOGDIR=$PATH_QLOG SSLKEYLOGFILE=$PATH_KEYS curl --http3 --local-port 4000 https://172.3.0.5:4433/echo -k --output /dev/null && QLOGDIR=$PATH_QLOG SSLKEYLOGFILE=/shared/keys/client_2.key curl --http3 --local-port 4001 https://172.3.0.5:4433 https://172.3.0.5:4433/echo -k --output /dev/null

# multiple Streams
QLOGDIR=$PATH_QLOG SSLKEYLOGFILE=$PATH_KEYS xargs -P 2 -n 1 curl --http3 --local-port 4000 https://172.3.0.5:4433/echo -Osk https://172.3.0.5:4433/echo -k --output /dev/null

#QLOGDIR=$PATH_QLOG SSLKEYLOGFILE=$PATH_KEYS xargs -P 2 -n 1 curl -Osk --http3 < curlsites.txt
#QLOGDIR=$PATH_QLOG SSLKEYLOGFILE=$PATH_KEYS curl --parallel --parallel-immediate --parallel-max 2 -Osk --http3 --config curlsites.txt


echo "client_curl: quic connection closed."

