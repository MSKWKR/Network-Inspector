#!/bin/sh

apt-get update
apt install curl -y
apt install isc-dhcp-client -y
apt install iproute2 -y 
apt install arp-scan -y 
apt install nmap -y 
apt install libxml2-utils -y 
apt install python3-pip -y 
apt install wireless-tools -y
apt install aircrack-ng -y 
pip install -r requirements.txt


curl -fsSL https://deb.nodesource.com/setup_16.x | bash - &&\
apt-get install nodejs -y
apt install npm -y 

cd web/server
npm install 
cd ../app
npm install 
cd ../../