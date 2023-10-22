#!/bin/bash

# Update ubuntu
apt update && 
apt upgrade -y &&

# Install dependencies
apt install git vim python-is-python3 pip curl iputils-ping net-tools bc iproute2 libssl-dev python3-dev nginx tcpdump iptables -y &&
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


# Install pandas
pip install pandas &&

# Install psutil
apt install python3-psutil



