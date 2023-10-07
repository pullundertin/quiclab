#!/bin/bash
PATH_KEYS=/shared/keys/server.key

echo "client: sending https request..."
SSLKEYLOGFILE=$PATH_KEYS curl https://172.3.0.5:443/data.log -k --output /dev/null
echo "client: https connection closed."
