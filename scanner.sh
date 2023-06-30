#!usr/bin/env bash

# Create log and lists folder
mkdir log &> /dev/null
mkdir lists &> /dev/null

# IP and mask of local machine
ip=$(hostname -I)	## grab ip using hostname -I
mask=$(ip a | grep $ip | awk '{print $2}')	## grab network mask using ip

# Responsive IPs and MAC Addresses
echo "Status: Initiating ARP scan..."
arp-scan -q -x $(echo $mask | sed 's/\.[0-9]*\//\.0\//g') | awk '{print $1}' | sort -u > ./lists/ip_list.txt	## arp-scan to pull ipv4 and mac from cache and store it in ip_list
echo "Status: ARP scan done."
echo "Status: Initiating ping scan..."
nmap -sn $mask --min-parallelism 10000 -T5 --host-timeout 5ms -oX ./log/ping_log.xml &> /dev/null	## ping scan the network for working ipv4 and mac, results stored in xml
echo "Status: Ping scan finished."
xmllint --xpath '//host/address[@addrtype="ipv4"]/@addr' ./log/ping_log.xml | cut -d '"' -f 2 >> ./lists/ip_list.txt	## parse xml file for ip and store it in ip_list.txt
sort -o ./lists/ip_list.txt -u ./lists/ip_list.txt	## sort out duplicate ip

# SMNP
snmp_scan(){
	echo "Status: Performing SNMP scan..."
	nmap -sU -p161 --script=snmp-info -iL ./lists/udp_list.txt --min-parallelism 10000 -T5 -oX ./log/snmp_log.xml &> /dev/null	## scan port 161(snmp) using script, results stored in xml
	echo "Status: SNMP scan done."
}

# DHCP
dhcp_scan(){
	echo "Status: Performing DHCP scan..."
	nmap -sU -p67-68 --script=dhcp-discover -iL ./lists/udp_list.txt --min-parallelism 10000 -T5 -oX ./log/dhcp_log.xml &> /dev/null	## scan port 67(dhcp) using script, results stored in xml
	echo "Status: DHCP scan done."
}

# Ports and Services
port_scan(){
	echo "Status: Probing for open ports..."
	nmap -sS -iL ./lists/ip_list.txt --min-parallelism 10000 -T5 -oX ./log/tcp_log.xml &> /dev/null &	## tcp port scan ip_list, results stored in xml
	### check what port protocols ip use
	nmap -sO -p17 -iL ./lists/ip_list.txt --min-parallelism 10000 -T5 -oX ./log/pp_log.xml &> /dev/null &	## port protocol scan ip_list to see if ip uses udp, results stored in xml
	wait
	xmllint --xpath '//address[@addrtype="ipv4"] | //port' ./log/pp_log.xml | grep -B 1 "open" | grep -i "ipv4" | cut -d '"' -f 2 > ./lists/udp_list.txt 
		## line above parses pp_log to search for IPs that uses UDP and stores it in udp_list 
	snmp_scan &
	dhcp_scan &	## run snmp and dhcp scan once udp_list is formed
	nmap -sU -iL ./lists/udp_list.txt --min-parallelism 10000 -T5 -oX ./log/udp_log.xml &> /dev/null 	## udp port scan udp_list, results stored in xml
	echo "Status: Ports and services acquired."
}

# OS
os_scan(){
	echo "Status: Scanning for Operating systems..."
	nmap -O -iL ./lists/ip_list.txt --min-parallelism 10000 -T5 -oX ./log/os_log.xml &> /dev/null	## os scan ip_list.txt, results stored in xml
	echo "Status: OS scan done."
}


port_scan &
os_scan &
wait
echo "Done"
