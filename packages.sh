#!/bin/sh

apt-get update
apt install curl -y
apt install isc-dhcp-client -y
apt install iproute2 -y #> /dev/null 2>&1
apt install arp-scan -y #> /dev/null 2>&1
apt install nmap -y #> /dev/null 2>&1
apt install libxml2-utils -y #> /dev/null 2>&1
apt install python3-pip -y #> /dev/null 2>&1
apt install wireless-tools -y
apt install aircrack-ng -y #> /dev/null 2>&1
pip install lxml=="4.9.2" #> /dev/null 2>&1
pip install beautifulsoup4=="4.12.2" #> /dev/null 2>&1


curl -fsSL https://deb.nodesource.com/setup_20.x | bash - &&\
apt-get install nodejs -y
apt install npm -y #> /dev/null 2>&1

cd web/server
npm install 
cd ../app
npm install 
cd ../../