#!usr/bin/env bash

# Create log and lists folder
mkdir log &> /dev/null
mkdir lists &> /dev/null

# IP and mask of local machine
ip=$(hostname -I)	## grab ip using hostname -I
mask=$(ip a | grep $ip | awk '{print $2}')	## grab network mask using ip ex: "127.xxx.xxx.xxx/xx"

# Responsive IPs and MAC Addresses
echo "Status: Initiating ARP scan..."
arp-scan -q -x $mask | awk '{print $1}' | sort -u > ./lists/ip_list.txt	## arp-scan to pull ipv4 and mac from cache and store it in ip_list
echo "Status: Initiating ping scan..."
nmap -sn $mask --min-parallelism 10000 -T5 --host-timeout 5ms -oX ./log/ping_log.xml &> /dev/null	## ping scan the network for working ipv4 and mac, results stored in xml
echo "Status: Ping scan finished."
xmllint --xpath '//host/address[@addrtype="ipv4"]/@addr' ./log/ping_log.xml | cut -d '"' -f 2 >> ./lists/ip_list.txt	## parse xml file for ip and store it in ip_list.txt
sort -o ./lists/ip_list.txt -u ./lists/ip_list.txt	## sort out duplicate ip

# DHCP
dhcp_scan(){
	dhcp_ip=$(journalctl -r | grep -i "dhcpack" | grep $(hostname) | awk '{print $10}')	## get dhcp server ip using journalctl
	if [[ -z "$dhcp_ip" ]]	## if ip found then proceed
	then
    	echo "Warning: No DHCP server found"
	else
    	echo "Status: Scanning DHCP server..."
		nmap -sU --script=dhcp-discover $dhcp_ip --min-parallelism 10000 -T5 -oX ./log/dhcp_log.xml &> /dev/null	## scan dhcp server ip with script, results stored in xml
		echo "Status: DHCP scan done".
		### check if dhcp server is in another network
		#if [[ ! $(grep $dhcp_ip ./lists/ip_list.txt) ]]
		#then
    		## run a scan in the network
		#fi
	fi
}

# Ports and Services
port_scan(){
	echo "Status: Probing for open ports..."
	nmap -sS -iL ./lists/ip_list.txt --min-parallelism 10000 -T5 -oX ./log/tcp_log.xml &> /dev/null &	## tcp port scan ip_list, results stored in xml
	### check what port protocols ip use
	nmap -sO -iL ./lists/ip_list.txt --min-parallelism 10000 -T5 -oX ./log/pp_log.xml &> /dev/null &	## port protocol scan ip_list to see if ip uses udp, results stored in xml
	wait
	xmllint --xpath '//service[@name="udp"] | //address[@addrtype="ipv4"]' ./log/pp_log.xml | grep -B 1 "udp" | grep -i "ipv4" | cut -d '=' -f 2 | cut -d '"' -f 2 > ./lists/udp_list.txt 
		## line above parses pp_log to search for IPs that uses UDP and stores it in udp_list 
	nmap -sU -iL ./lists/udp_list.txt --min-parallelism 10000 -T5 -oX ./log/udp_log.xml &> /dev/null 	## udp port scan udp_list, results stored in xml
	echo "Status: Ports and services acquired."
}

# OS
os_scan(){
	echo "Status: Scanning for Operating systems..."
	nmap -O -iL ./lists/ip_list.txt --min-parallelism 10000 -T5 -oX ./log/os_log.xml &> /dev/null	## os scan ip_list.txt, results stored in xml
	echo "Status: OS scan done."
}

dhcp_scan &
port_scan &
os_scan &
wait
echo "Done"
