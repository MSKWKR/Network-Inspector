#!/bin/sh


main() {
	set_env
	lease_ip
	dhcp_scan "./log/dhcp_log.xml" 
	arp_scan "./lists/ip_list.txt"
	ping_scan "./lists/ip_list.txt" "./log/ping_log.xml"
	dns_scan "./lists/domain_list.txt" "./log/dhcp_log.xml" "./log/dns_log.xml" &
	tcp_scan "./lists/ip_list.txt" "./log/tcp_log.xml" &
	udp_dependent &
	wait
}

# Function: set_env
# Description: Make directories.
set_env() {
		mkdir log > /dev/null 2>&1
		mkdir lists > /dev/null 2>&1
}

# Function: lease_ip
# Description: Lease ip from dhcp server and check for dhcp server ip at the same time.
lease_ip() {
		echo "Status: Checking for network interfaces..."
		# Check which network interface is up
		interface="$(ip a | grep "state UP" | awk '{print $2}' | cut -d ':' -f 1)"
		if [ "$interface" ]; then
			echo "Status: Interface: $interface is up."
			# Check for dhcp server in network, if true then lease an ip
			echo "Status: Leasing for IP..."
			dhcp="$(dhclient -v "$interface" 2>&1 | grep DHCPOFFER | awk '{print $5}')"
			if [ "$dhcp" ]; then
				echo "Status: IP acquired from DHCP server."
			else
				dhcp="$(dhclient -v "$interface" 2>&1 | grep DHCPACK | awk '{print $5}')"
				if [ "$dhcp" ]; then
					echo "Status: IP acknowledged by DHCP server."
				else
					echo "Warning: Unable to lease ip, DHCP server might be down."
					exit 1
				fi
			fi
			# Get local machine ip and network mask
			ip="$(ip a | grep "$interface" | grep "inet " | awk '{print $2}' | cut -d '/' -f 1)"
			mask="$(ip r | grep "$ip" | awk '{print $1}')"
		else
			echo "Warning: No network interface connected."
			exit 1
		fi
}

# Function: arp_scan
# Description: Find ip from arp-scan and output into a list.
# Parameters: 
#	$1 - Path to output ip list. 
arp_scan() {
	_output_list=$1
	echo "Status: Initiating ARP scan..."
	# arp-scan to pull ipv4 and store it in ip_list
	arp-scan -q -x "$mask" | awk '{print $1}' | sort -u > "$_output_list"
	echo "Status: ARP scan done."
}

# Function: ping_scan
# Description: Find responsive addresses using nmap ping scan and output into a list.
# Parameters:
#	$1 - Path to output ip list.
#	$2 - Path to output ping_scan log.
ping_scan() {
	_output_list=$1
	_output_log=$2
	echo "Status: Initiating ping scan..."
	# Ping scan the network using multiple methods for working ips, results stored in xml
	nmap -sn -PR -PE -PS443 -PA80 -PP "$mask" -T3 -oX "$2" > /dev/null 2>&1
	# Parse xml file for ip and store it in ip_list
	xmllint --xpath '//host/address[@addrtype="ipv4"]/@addr' "$2" | cut -d '"' -f 2 >> "$1"
	# Sort out duplicates
	sort -o "$1" -u "$1"
	echo "Status: Ping scan finished."
}

# Function: snmp_scan
# Description: Run multiple nmap scripts to find snmp info, time consuming.
# Parameters:
#	$1 - Path to input ip list.
#	$2 - Path to output snmp_scan log.
snmp_scan() {
	echo "Status: Performing SNMP scan..."
	# Scan for every snmp information possible, this will take a long time
	nmap -Pn -sU -p161 -n --script=snmp-info --script=snmp-interfaces --script=snmp-processes --script=snmp-sysdescr --script=snmp-win32-software -iL "$1" -T3 --disable-arp-ping -oX "$2" > /dev/null 2>&1
	echo "Status: SNMP scan done."
}

# Function: dhcp_scan
# Description: Run nmap dhcp discovery script to find out more info from dhcp server.
# Parameters:
#	$1 - Path to output dhcp_scan log.
dhcp_scan() {
	echo "Status: Performing DHCP scan..."
 	# Scan port 67(dhcp) using script, results stored in xml
	nmap -Pn -sU -p67 -n --script=dhcp-discover "$dhcp" -T3 --disable-arp-ping -oX "$1" > /dev/null 2>&1
	echo "Status: DHCP scan done."
}

# Function: dns_scan
# Description: Run nmap dns service discovery script to get service info hidden in dns, and pull dns cache domains.
# Parameters: 
#	$1 - Path to input domain list.
#	$2 - Path to input dhcp_scan log.
#	$3 - Path to output dns_scan log.
dns_scan() {
	echo "Status: Scanning for DNS services..."
	# Parse out dns server ip from dhcp_log
	ns="$(xmllint --xpath '//table[@key="Domain Name Server"]/elem/text()' "$2" | sort -u)"
	# Read domains from domain_list
	filename="$1"
	domain='domain'
	while read -r line; do
		domain="${domain},$line"
	done < "$filename"
	nmap --script=broadcast-dns-service-discovery -sU -p53 --script dns-cache-snoop.nse --script-args dns-cache-snoop.domains="{$domain}" $ns -oX "$3" > /dev/null 2>&1
	echo "Status: DNS scan done."
}

# Function: tcp_scan
# Description: Scan for service info about tcp ports, time consuming. 
# Parameters:
#	$1 - Path to input ip list.
#	$2 - Path to output tcp_scan log.
tcp_scan() {
	echo "Status: Scanning TCP ports..."
	nmap -Pn -sS -sV --version-intensity 2 -iL "$1" -T4 --min-parallelism 100 --defeat-rst-ratelimit --disable-arp-ping -oX "$2" > /dev/null 2>&1
	echo "Status: Finished TCP scanning."
}

# Function: udp_scan
# Description: Scan for service info about udp ports, time consuming. 
# Parameters:
#	$1 - Path to input udp list.
#	$2 - Path to output udp_scan log.
udp_scan() {
	echo "Status: Scanning UDP ports..."
	nmap -Pn -sU -n -sV --version-intensity 2 -iL "$1" -T3 --max-rtt-timeout 100ms --defeat-icmp-ratelimit --disable-arp-ping -oX "$2" > /dev/null 2>&1 	## udp port scan udp_list, results stored in xml
	echo "Status: Finished UDP scanning."
}

# Function: pp_scan
# Description: Scan for addresses that uses udp protocol.
# Parameters:
#	$1 - Path to input ip list.
#	$2 - Path to output port protocol log.
#	$3 - Path to output udp list.
pp_scan() {
	nmap -Pn -sO -p17 -n -iL "$1" -T3 -oX "$2" > /dev/null 2>&1
	# Parse pp_log to search for IPs that uses UDP and stores it in udp_list
	xmllint --xpath '//address[@addrtype="ipv4"] | //port' ./log/pp_log.xml | grep -B 1 "open" | grep -i "ipv4" | cut -d '"' -f 2 > "$3" 	
}

# Function: udp_dependent
# Description: Run pp_scan first then udp_scan and snmp_scan in parallel.
udp_dependent() {
	pp_scan "./lists/ip_list.txt" "./log/pp_log.xml" "./lists/udp_list.txt"
	udp_scan "./lists/udp_list.txt" "./log/udp_log.xml" &
	snmp_scan "./lists/udp_list.txt" "./log/snmp_log.xml" &
}

# Function: wlan_scan
# Description: Monitor all wireless connections around local machine.
# Parameters:
#	$1 - Path to output wlan_scan log.
wlan_scan() {
	wlan="$(lshw -C network | grep -B 3 -i "wireless" | grep -i "logical name" | awk '{print $3}')"
	airmon-ng check kill > /dev/null 2>&1
	wlan="$(airmon-ng start "$wlan" | grep enabled | awk '{print $7}' | cut -d ']' -f 2)"
	timeout --foreground 60 airodump-ng "$wlan" --output-format netxml -w ./log/wlan_log > /dev/null 2>&1
	airmon-ng stop "$wlan" > /dev/null 2>&1
	echo "Done"
}


main
echo "Status: Running Parser..."
python3 log_parser.py