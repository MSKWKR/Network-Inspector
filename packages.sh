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
pip install lxml=="4.9.2" 
pip install beautifulsoup4=="4.12.2" 


curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&\
apt-get install nodejs -y
apt install npm -y 

cd web/server
npm install 
cd ../app
npm install 
cd ../../