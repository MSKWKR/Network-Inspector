#!/bin/sh

sudo apt install arp-scan -y #> /dev/null 2>&1
sudo apt install nmap -y #> /dev/null 2>&1
sudo apt install libxml2-utils -y #> /dev/null 2>&1
sudo apt install python3-pip -y #> /dev/null 2>&1
sudo apt install aircrack-ng -y #> /dev/null 2>&1

curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - &&\
sudo apt-get install nodejs -y
sudo apt install npm -y #> /dev/null 2>&1

npm install express typescript ts-node
npm i @types/node @types/express
npm init -y

pip install lxml=="4.9.2" #> /dev/null 2>&1
pip install beautifulsoup4=="4.12.2" #> /dev/null 2>&1

##npx tsc app.ts
##sudo node app.js