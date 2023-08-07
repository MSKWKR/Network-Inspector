## Environment:
**Ubuntu: 22.04**  
**Python: 3.10.6**  

## Local Installation & Setup:
```sh
    sudo bash package.sh
    sudo bash setup.sh 
```

## Docker Installation & Setup:
```sh
    docker pull network-inspector:latest
    docker run --network=host --privileged network-inspector:latest ./setup.sh
```

## Usage:
**After setup visit [Here](http://localhost:3000) for a list of available JSON files.**  
**Run [This](http://localhost:3000/trigger) to trigger a scan.**    
**To visit the REACT app manually: http://localhost:3000.**    
**To trigger the scan manually: http://localhost:80/trigger.**  

## Structure:
```
├── json
│   └── sample.json
├── lists
│   ├── domain_list.txt
│   ├── ip_list.txt
│   └── udp_list.txt
├── log
│   ├── dhcp_log.xml
│   ├── dns_log.xml
│   ├── ping_log.xml
│   ├── pp_log.xml
│   ├── snmp_log.xml
│   ├── tcp_log.xml
│   ├── udp_log.xml
│   └── wlan_log.xml
├── packages.sh
├── setup.sh
├── utils
│   ├── log_parser.py
│   └── scanner.sh
└── web
    ├── app
    │   ├── package.json
    │   ├── package-lock.json
    │   └── src
    │       ├── App.css
    │       ├── App.js
    │       └── index.js
    └── server
        ├── index.js
        ├── index.ts
        ├── package.json
        └── package-lock.json
```
