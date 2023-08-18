# Network-Inspector

## Build Environment
> ubuntu 22.04  
> python 3.10.6  
> node 16

## Dependencies
> ### scanner.sh:
> * **iproute2**: For basic commands such as `ip addr` & `ip route`.
> * **isc-dhcp-client**: For the command `dhclient` which leases ip from DHCP server and the creation of _`dhclient.leases`_.
> * [**arp-scan**](#arp-scan): Get MAC and ip addresses using `arp-scan`.
> * [**nmap**](#nmap): Multiple wired scanning methods using `nmap`.
> * **wireless-tools**: For basic commands like `iwconfig`.
> * [**aircrack-ng**](#aircrack-ng): Monitor wireless connections using `airmon-ng` & `airodump-ng`  
> :warning: dependent on **pcutils** & **kmod**. 
> * [**libxml2-utils**](#xmllint): For the command `xmllint` for basic xml parsing.
> ### nodejs server:
> * [**nodejs**](https://nodejs.org/en): Install Nodejs directly from source using curl.  
> `curl -fsSL https://deb.nodesource.com/setup_16.x | bash -`
> * **npm**:
>> * [**express**](https://expressjs.com/): Api built using express.
>> * **path**: For local file path finding.
>> * **child_process**: For running local files.
>> * **cors**: To give frontend access permission.
> ### log_parser.py:
> * [**beautifulsoup4**](#beautifulsoup4): Main xml parsing tool.  
> `pip install lxml=="4.9.2" beautifulsoup4=="4.12.2"`

## Installation & Setup:
> ### [Local installation](https://dev.azure.com/FreedomSystems/tech-voyager/_git/network-inspector)
> ```sh
> git clone -b local https://FreedomSystems@dev.azure.com/FreedomSystems/tech-voyager/_git/network-inspector
> sudo bash package.sh
> sudo bash setup.sh 
> ```
> ### [Docker image](https://hub.docker.com/repository/docker/mskwkr/network-inspector-script/general)
> ```sh
> docker pull mskwkr/network-inspector:tagname
> docker run --network=host --privileged mskwkr/network-inspector:tagname ./setup.sh
> ```

## Usage:
> After installation and setup visit http://localhost:3000 to access the REACT app.  
> To trigger a scan visit http://localhost:3000/trigger.  
> For remote login, type `nslookup FDS-netspctr` into the terminal for **device ip**, then visit http://**device ip**:3000.  
> :warning: Make sure prior scan is finished before triggering another, or else the results would have discrepancies.  

## Manual for modules
> ### [**nmap**](https://nmap.org/)
> ```sh
> -sn : # ping scan, pinging hosts without doing port scan
> -PR : # send raw ARP requests
> -PE : # enable ICMP request
> -PP : # send ICMP request
> -PS <num> : # send TCP SYN packet to the port specified, default is port 80
> -PA <num> : # send TCP ACK packet to the port specified, default is port 80
> -sS : # TCP SYN scan, scan stealthily by return RST instead of ACK
> -sU : # UDP scan
> -sO : # IP protocol scan, scan for protocols in use
> -sV : # scan ports for service details
> --version-intensity <0~9> : # define how accurate the service scan wil be, higher is slower
> -O : # OS scan, returns the "chance" of operating system in use
> -p <num> : # specify which port to scan
> -T<1~5> : # increase speed of process by reducing retries and delay time, higher is faster
> --host-timeout <time> : # wait time till timeout
> --min-host-group <num> : # the minimum amount of hosts to scan in parallel
> --min-parallelism <num> : # the minimum amount of probes to send to each port, more probes mean faster confirmation 
> -iL <file_path> : # only scan listed hosts
> -oX <file_path> : # export results to file in xml format
> --script <script> : # pull script from nmap index
> --disable-arp-ping : # remove arp scan from discovery stage
> --defeat-rst-ratelimit : # during TCP scan treat non-responsive ports as closed to reduce time
> --defeat-icmp-ratelimit : # during UDP scan treat non-responsive ports as closed|filtered to reduce time
> --max-rtt-timeout <time> : # if response time is longer than <time>, then treat as non-responsive
> ```
> ### [**arp-scan**](https://github.com/royhills/arp-scan)
> ```sh
> -q : # remove device name from output
> -x : # remove header and footer from output
> ```
> ### [**aircrack-ng**](https://www.aircrack-ng.org/)
> `airmon-ng check kill` : check for and remove processes that affects wireless monitoring  
> `airmon-ng start <interface>` : start wireless monitoring on specified interface  
> `airmon-ng stop <interface>` : stop wireless monitoring on specified interface  
> `airodump-ng <interface>` : show monitoring results, this is a continuous output like `tcpdump`
> ### [**xmllint**](https://www.baeldung.com/linux/xmllint)
> ```sh
> --xpath <path_and_patterns> : # output selected parameters from xml
> --format : # show xml hierarchy
> ```
> ### [**beautifulsoup4**](https://pypi.org/project/beautifulsoup4/)
> ```py
> .find("tag") : # find the first instance of the tag in xml
> .find("tag", {"attribute": "attribute_value"}) : # find matching value of the attribute in tag
> .find_all("tag") : # find all instances of the tag and return list
> .get("attribute") : # grab the attribute value in xml
> ```
> ### mischellaneous
> #### grep
> ```sh
> -i : # ignore upper case and lower case
> -B <num> : # include lines above
> ```
> #### cut
> ```sh
> -d 'char' : # cut string base on 'char'
> -f <num> : # output the section of the cut
> ```
> #### awk
> ```sh
> '{print $<num>}' : # output part of the string base on whitespace
> ```
> #### sort
> ```sh
> -o : # output
> -u : # remove duplicates
> ```

## File structure:
> ```
> ├── README.md
> ├── workflow.drawio
> ├── Dockerfile.infra
> ├── Dockerfile.script
> ├── docker-compose.yml
> ├── json
> │   └── sample.json
> ├── lists
> │   ├── domain_list.txt
> │   ├── ip_list.txt
> │   └── udp_list.txt
> ├── log
> │   ├── dhcp_log.xml
> │   ├── dns_log.xml
> │   ├── ping_log.xml
> │   ├── pp_log.xml
> │   ├── snmp_log.xml
> │   ├── tcp_log.xml
> │   ├── udp_log.xml
> │   └── wlan_log.xml
> ├── packages.sh
> ├── setup.sh
> ├── utils
> │   ├── log_parser.py
> │   └── scanner.sh
> └── web
>     ├── app
>     │   ├── README.md
>     │   ├── package-lock.json
>     │   ├── package.json
>     │   ├── public
>     │   │   ├── favicon.ico
>     │   │   └── index.html
>     │   └── src
>     │       ├── App.css
>     │       ├── App.js
>     │       └── index.js
>     └── server
>         ├── index.js
>         ├── index.ts
>         ├── package-lock.json
>         └── package.json
> ```
