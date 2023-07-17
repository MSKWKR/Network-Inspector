#!/bin/sh

if [ "$(dpkg -s arp-scan | grep "Version:" | awk '{print $2}')" != "1.9.7-2" ]; then
	apt install arp-scan=1.9.7-2 -y #> /dev/null 2>&1
fi
if [ "$(dpkg -s nmap | grep -i "Version:" | awk '{print $2}')" != "7.91+dfsg1+really7.80+dfsg1-2ubuntu0.1" ]; then
	apt install nmap=7.91+dfsg1+really7.80+dfsg1-2ubuntu0.1 -y #> /dev/null 2>&1
fi
if [ "$(dpkg -s libxml2-utils | grep "Version:" | awk '{print $2}')" != "2.9.13+dfsg-1ubuntu0.3" ]; then
	apt install libxml2-utils=2.9.13+dfsg-1ubuntu0.3 -y #> /dev/null 2>&1
fi
if [ "$(dpkg -s python3-pip | grep "Version:" | awk '{print $2}')" != "22.0.2+dfsg-1ubuntu0.3" ]; then
	apt install python3-pip=22.0.2+dfsg-1ubuntu0.3 -y #> /dev/null 2>&1
fi
if [ "$(dpkg -s aircrack-ng | grep "Version:" | awk '{print $2}')" != "1:1.6+git20210130.91820bc-2" ]; then
	apt install aircrack-ng=1:1.6+git20210130.91820bc-2 -y #> /dev/null 2>&1
fi
if [ "$(pip show lxml | grep "Version:" | awk '{print $2}')" != "4.9.2" ]; then
	pip install lxml=="4.9.2" #> /dev/null 2>&1
fi
if [ "$(pip show beautifulsoup4 | grep "Version:" | awk '{print $2}')" != "4.12.2" ]; then
	pip install beautifulsoup4=="4.12.2" #> /dev/null 2>&1
fi