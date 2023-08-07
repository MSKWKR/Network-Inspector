#!/bin/sh

main() {
	set_var
	[ "$wlan" ] && wlan_scan "./log/wlan_log.xml" &
	[ "$dhcp" ] && dhcp_scan "./log/dhcp_log.xml" &
	if [ "$ip" ]; then
		arp_scan "./lists/ip_list.txt"
		ping_scan "./lists/ip_list.txt" "./log/ping_log.xml"
		dns_scan "./lists/domain_list.txt" "./log/dhcp_log.xml" "./log/dns_log.xml" &
		tcp_scan "./lists/ip_list.txt" "./log/tcp_log.xml" &
		udp_dependent 
	fi
	wait
}

# Function: set_var
# Description: Setup common variables
set_var() {
	echo "Status: Setting variables..."
	interface="$(ip addr | grep "state UP" | awk '{print $2}' | cut -d ':' -f 1)"
	echo "got interface $interface"
	wlan="$(iwconfig 2>&1 | grep "IEEE" | awk '{print $1}')"
	echo "got wlan $wlan"
	dhcp="$(cat /var/lib/dhcp/dhclient.leases | grep dhcp-server-identifier | awk '{print $3}' | cut -d ';' -f 1)"
	echo "got dhcp $dhcp"
	ip="$(ip r | grep "$interface" | grep src | awk '{print $9}')"
	echo "got ip $ip"
	mask="$(ip r | grep "$ip" | awk '{print $1}')"
	echo "got mask $mask"
	echo "Status: Finished setting variables."
}

# Function: arp_scan
# Description: Find ip from arp-scan and output into a list.
# Parameters: 
#	$1 - Path to output ip list. 
arp_scan() {
	echo "Status: Initiating ARP scan..."
	# arp-scan to pull ipv4 and store it in ip_list
	arp-scan -q -x "$mask" | awk '{print $1}' | sort -u > "$1"
	echo "Status: ARP scan done."
}

# Function: ping_scan
# Description: Find responsive addresses using nmap ping scan and output into a list.
# Parameters:
#	$1 - Path to output ip list.
#	$2 - Path to output ping_scan log.
ping_scan() {
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
	nmap -sU -p161 -n --script=snmp-info --script=snmp-interfaces --script=snmp-processes --script=snmp-sysdescr --script=snmp-win32-software -iL "$1" -T4 --min-hostgroup 100 --min-parallelism 100 -oX "$2" > /dev/null 2>&1
	echo "Status: SNMP scan done."
}

# Function: dhcp_scan
# Description: Run nmap dhcp discovery script to find out more info from dhcp server.
# Parameters:
#	$1 - Path to output dhcp_scan log.
dhcp_scan() {
	echo "Status: Performing DHCP scan..."
 	# Scan port 67(dhcp) using script, results stored in xml
	nmap -sU -p67 -n --script=dhcp-discover "$dhcp" -T3 -oX "$1" > /dev/null 2>&1
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
	nmap -sS -sV --version-intensity 2 -iL "$1" -T4 --min-hostgroup 100 --min-parallelism 100 --defeat-rst-ratelimit -oX "$2" > /dev/null 2>&1
	echo "Status: Finished TCP scanning."
}

# Function: udp_scan
# Description: Scan for service info about udp ports, time consuming. 
# Parameters:
#	$1 - Path to input udp list.
#	$2 - Path to output udp_scan log.
udp_scan() {
	echo "Status: Scanning UDP ports..."
	nmap -sU -sV --version-intensity 2 -iL "$1" -T4 --min-hostgroup 100 --min-parallelism 100 --defeat-icmp-ratelimit -oX "$2" > /dev/null 2>&1 	## udp port scan udp_list, results stored in xml
	echo "Status: Finished UDP scanning."
}

# Function: pp_scan
# Description: Scan for addresses that uses udp protocol.
# Parameters:
#	$1 - Path to input ip list.
#	$2 - Path to output port protocol log.
#	$3 - Path to output udp list.
pp_scan() {
	nmap -sO -p17 -n -iL "$1" -T4 -oX "$2" > /dev/null 2>&1
	# Parse pp_log to search for IPs that uses UDP and stores it in udp_list
	xmllint --xpath '//address[@addrtype="ipv4"] | //port' "$2" | grep -B 1 "open" | grep -i "ipv4" | cut -d '"' -f 2 > "$3" 	
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
	echo "Status: Monitoring wireless network..."
	airmon-ng check kill > /dev/null 2>&1
	airmon-ng start "$wlan" > /dev/null 2>&1
	wlan="$(iwconfig 2>&1 | grep "IEEE" | awk '{print $1}')"
	timeout --foreground 120 airodump-ng "$wlan" --output-format netxml -w "$1" > /dev/null 2>&1
	airmon-ng stop "$wlan" > /dev/null 2>&1
	[ "$1-01.kismet.netxml" ] && mv "$1-01.kismet.netxml" "$1" || echo "WIRELESS MONITORING ERROR."
	echo "Status: Finished monitoring wireless network."
}


main
echo "Status: Running Parser..."
python3 ./utils/log_parser.py
exit 1