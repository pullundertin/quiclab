#!/bin/bash

# Update ubuntu
apt update && 
apt upgrade -y &&

# Install dependencies
apt install git vim npm -y &&

# Install qvis
git clone https://github.com/quiclog/qvis.git &&
cd /qvis/visualizations/ &&

# Install npm
npm install







