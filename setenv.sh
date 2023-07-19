#!/bin/sh

sudo apt install arp-scan -y #> /dev/null 2>&1
sudo apt install nmap -y #> /dev/null 2>&1
sudo apt install libxml2-utils -y #> /dev/null 2>&1
sudo apt install python3-pip -y #> /dev/null 2>&1
sudo apt install aircrack-ng -y #> /dev/null 2>&1

pip install lxml=="4.9.2" #> /dev/null 2>&1
pip install beautifulsoup4=="4.12.2" #> /dev/null 2>&1
