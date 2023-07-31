#!/bin/sh

run_script=false
check_connection() {
	interface="$(ip a show enp1s0 | grep "state UP" | awk '{print $2}' | cut -d ':' -f 1)"
	if [ "$interface" ]; then
		# Check for dhcp server in network, if true then lease an ip
		dhcp="$(dhclient -v "$interface" 2>&1 | grep "DHCPOFFER\|DHCPACK" | awk '{print $5}' | sort -u)"
        [ -z "$dhcp" ] && exit 1
	else
		exit 1
	fi
}

while true; do
    if ip link show enp1s0 | grep "state UP"; then
        if ! $run_script; then
            check_connection
            cd web/server
            node index.js &
            cd ../app
            npm start
            # python3 -m webbrowser http://172.16.7.121:80/trigger
        fi
    fi
    sleep 1
done

