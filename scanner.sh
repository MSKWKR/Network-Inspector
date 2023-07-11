#!usr/bin/env bash

# Create log and lists folder
mkdir log &> /dev/null
mkdir lists &> /dev/null


# Check which network interface is up
echo "Status: Checking for network interfaces..."
interface=$(ip a | grep "state UP" | awk {'print $2'} | cut -d ':' -f 1)
if [ $interface ] 
then
	echo "Status: Interface: $interface is up."
	# Check for dhcp server in network, if true then lease an ip
	echo "Status: Leasing for IP..."
	dhcp=$(dhclient -v $interface |& grep DHCPOFFER | awk {'print $5'})
	if [ $dhcp ]
	then
		echo "Status: IP acquired from DHCP server."
	else
		dhcp=$(dhclient -v $interface |& grep DHCPACK | awk {'print $5'})
		if [ $dhcp ]
		then
			echo "Status: IP acknowledged by DHCP server."
		else
			echo "Warning: Unable to lease ip, DHCP server might be down."
			exit 1
		fi
	fi
else
	echo "Warning: No network interface connected."
	exit 1
fi

# IP and mask of local machine
ip=$(ip a | grep $interface | grep "inet " | awk {'print $2'} | cut -d '/' -f 1)	## grab ip that is connected to internet
mask=$(ip r | grep $ip | awk '{print $1}')	## grab network mask

# Responsive IPs and MAC Addresses
echo "Status: Initiating ARP scan..."
arp-scan -q -x $mask | awk '{print $1}' | sort -u > ./lists/ip_list.txt	## arp-scan to pull ipv4 and mac from cache and store it in ip_list
echo "Status: ARP scan done."
echo "Status: Initiating ping scan..."
nmap -sn $mask --min-parallelism 10000 -T5 --host-timeout 5ms -oX ./log/ping_log.xml &> /dev/null	## ping scan the network for working ipv4 and mac, results stored in xml
echo "Status: Ping scan finished."
xmllint --xpath '//host/address[@addrtype="ipv4"]/@addr' ./log/ping_log.xml | cut -d '"' -f 2 >> ./lists/ip_list.txt	## parse xml file for ip and store it in ip_list.txt
sort -o ./lists/ip_list.txt -u ./lists/ip_list.txt	## sort out duplicate ip

# SMNP
snmp_scan(){
	echo "Status: Performing SNMP scan..."
	## scanning for every snmp information possible, this will take a long time
	nmap -Pn -sU -p161 -n --script=snmp-info --script=snmp-interfaces --script=snmp-processes --script=snmp-sysdescr --script=snmp-win32-software -iL ./lists/udp_list.txt --min-parallelism 10000 -T5 --disable-arp-ping -oX ./log/snmp_log.xml &> /dev/null	## scan port 161(snmp) using script, results stored in xml
	echo "Status: SNMP scan done."
}

# DHCP
dhcp_scan(){
	echo "Status: Performing DHCP scan..."
	nmap -Pn -sU -p67 -n --script=dhcp-discover $dhcp --min-parallelism 10000 -T5 --disable-arp-ping -oX ./log/dhcp_log.xml &> /dev/null	## scan port 67(dhcp) using script, results stored in xml
	echo "Status: DHCP scan done."
	dns_scan &
}

# DNS
dns_scan(){
	echo "Status: Scanning for DNS services..."
	ns=$(xmllint --xpath '//table[@key="Domain Name Server"]/elem/text()' ./log/dhcp_log.xml | sort -u)	## parse out dns server ip from dhcp_log
	## read top 1000 domains from domain_list
	filename='./lists/domain_list.txt'
	domain='domain'
	while read line; do
		domain+=,$line
	done < $filename
	## get dns services and dns cache domains
	nmap --script=broadcast-dns-service-discovery -sU -p53 --script dns-cache-snoop.nse --script-args dns-cache-snoop.domains={$domain} $ns -oX ./log/dns_log.xml &> /dev/null
	echo "Status: DNS scan done."
}

# TCP
tcp_scan(){
	echo "Status: Scanning TCP ports..."
	nmap -Pn -sS -sV --version-intensity 2 -iL ./lists/ip_list.txt --min-parallelism 10000 -T5 --defeat-rst-ratelimit --disable-arp-ping -oX ./log/tcp_log.xml &> /dev/null	## tcp port scan ip_list, results stored in xml
	echo "Status: Finished TCP scanning."
}

# Port Protocol
pp_scan(){
	### check what port protocols ip use
	nmap -Pn -sO -p17 -n -iL ./lists/ip_list.txt --min-parallelism 10000 -T5 -oX ./log/pp_log.xml &> /dev/null	## port protocol scan ip_list to see if ip uses udp, results stored in xml
	xmllint --xpath '//address[@addrtype="ipv4"] | //port' ./log/pp_log.xml | grep -B 1 "open" | grep -i "ipv4" | cut -d '"' -f 2 > ./lists/udp_list.txt 
		## line above parses pp_log to search for IPs that uses UDP and stores it in udp_list	
}

# UDP
udp_scan(){
	echo "Status: Scanning UDP ports..."
	nmap -Pn -sU -n -sV --version-intensity 2 -iL ./lists/udp_list.txt --min-parallelism 10000 -T5 --max-rtt-timeout 100ms --defeat-icmp-ratelimit --disable-arp-ping -oX ./log/udp_log.xml &> /dev/null 	## udp port scan udp_list, results stored in xml
	echo "Status: Finished UDP scanning."
}

# Ports and Services
port_scan(){
	echo "Status: Probing for open ports..."
	tcp_scan &
	pp_scan
	snmp_scan &
	dhcp_scan &	## run snmp and dhcp scan once udp_list is formed
	udp_scan
	wait
	echo "Status: Ports and services acquired."
}

# OS
os_scan(){
	echo "Status: Scanning for Operating systems..."
	nmap -Pn -O -iL ./lists/ip_list.txt --min-parallelism 10000 -T5 -oX ./log/os_log.xml &> /dev/null	## os scan ip_list.txt, results stored in xml
	echo "Status: OS scan done."
}


port_scan &
os_scan &
wait
echo "Done"
