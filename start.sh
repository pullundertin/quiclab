#!/bin/bash

WORKDIR="/root/test_env/shared"


rm -r $WORKDIR/* && echo 'All files deleted.'

docker-compose down
docker-compose up -d

file=$WORKDIR'/interfaces.log'


###### CLIENT ########

# fetch interface number
match=$(cat $file | sed -n '/client: /p')
number_iflink=$(echo $match | awk '{print $2}')

# search interface number and get interface name
name_iflink=$(ip a s | grep $number_iflink | awk -F $number_iflink': |@' '{print $2}' | awk 'NF')
# replace number with name
cat $file | sed -i "s|$number_iflink|$name_iflink|" $file


##### SERVER #####

# fetch interface number
match=$(cat $file | sed -n '/server: /p')
number_iflink=$(echo $match | awk '{print $2}')

# search interface number and get interface name
name_iflink=$(ip a s | grep $number_iflink | awk -F $number_iflink': |@' '{print $2}' | awk 'NF')

# replace number with name
cat $file | sed -i "s|$number_iflink|$name_iflink|" $file

echo "############# Info Wireshark #############"

cat $file


echo "############# Container ###############"

docker container ls
