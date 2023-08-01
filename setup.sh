#!/bin/sh

main() {
    dir_setup
    wlan_setup
    server_setup
}

# Function: dir_setup
# Description: Make directories for file storage.
dir_setup() {
    # Make directories
    [ -d "./log" ] || mkdir ./log
    [ -d "./lists" ] || mkdir ./lists
}

# Function: wlan_setup
# Description: Reset wireless network monitoring.
wlan_setup() {
    # Check for wireless card
    wlan="$(iwconfig |& grep "IEEE" | awk '{print $1}')"
    if [ "$wlan" ]; then
    	# Check if network card is in monitor mode
    	airmon_check="$(ip addr show "$wlan" | grep radiotap)"
    	[ "$airmon_check" ] && airmon-ng stop "$wlan" >/dev/null 2>&1
    else
    	echo "MISSING WIRELESS NETWORK CARD."
    fi
}

# Function: server_setup
# Description: Check for LAN interface and setup server.
server_setup() {
    server_stat=false

    while true; do
        # Check which interface is plugged in
        interface="$(ip addr | grep "state UP" | awk '{print $2}' | cut -d ':' -f 1)"
        if [ "$interface" ]; then
            # Check if server is up
            if ! $server_stat; then
                # Check for dhcp server in network, if true then lease an ip
    		    dhcp="$(dhclient -v "$interface" 2>&1 | grep "DHCPOFFER\|DHCPACK" | awk '{print $5}' | sort -u)"
                if [ "$dhcp" ]; then
                    # Setup server and app
                    node ./web/server/index.js &
                    cd ./web/app
                    npm start &
                    pwd
                    wait
                else
                    echo "NO DHCP SERVER FOUND."
                fi
            fi
        else
            echo "RETRYING."
            sleep 1
        fi
    done
}


main