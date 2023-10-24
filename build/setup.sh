#!/bin/bash

# Update ubuntu
apt update && 
apt upgrade -y &&

# Install dependencies
apt install git vim python-is-python3 pip curl iputils-ping net-tools bc iproute2 libssl-dev python3-dev nginx tcpdump wget iptables -y &&
# apt install DEBIAN_FRONTEND=noninteractive apt-get install -y tzdata &&

# Install aioquic
git clone https://github.com/aiortc/aioquic.git &&
pip install aioquic &&
cd /aioquic &&
pip install --upgrade pip setuptools &&
pip install -e . &&
pip install asgiref dnslib "flask<2.2" httpbin starlette "werkzeug<2.1" wsproto &&

# Prepare nginx
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /example.key -out /example.crt -subj "/C=DE/ST=Berlin/L=GERMANY/O=Dis/CN=www.example.com" &&
ln -s /data/data.log /var/www/html/data.log &&

# Install quic-go
cd / &&
git clone https://github.com/quic-go/quic-go.git &&

# install go
cd / &&

architecture=$(uname -m)

if [ "$architecture" == "x86_64" ]; then
    wget https://go.dev/dl/go1.21.3.linux-amd64.tar.gz &&
    rm -rf /usr/local/go && tar -C /usr/local -xzf go1.21.3.linux-amd64.tar.gz
elif [ "$architecture" == "aarch64" ]; then
    wget https://go.dev/dl/go1.21.3.linux-arm64.tar.gz
    rm -rf /usr/local/go && tar -C /usr/local -xzf go1.21.3.linux-arm64.tar.gz
else
    echo "The architecture is not recognized: $architecture"
fi

ln -s /usr/local/go/bin/go /usr/bin/go &&

cd quic-go &&
go get -d ./... &&

# Install pandas
pip install pandas &&

# Install psutil
apt install python3-psutil



