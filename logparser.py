#!usr/bin/env python

from bs4 import BeautifulSoup

# create data dictionary to store all data, and ipv4 list
data_dict = {}
ipv4_list = []

# turn ip_list.txt into ipv4 list     
with open('./lists/ip_list.txt', 'r') as f:
    file = f.readlines()
    for line in file:
        ipv4_list.append(line.strip()) 
    ## create a dictionary for each ip address in data_dict
    for ip in ipv4_list:
        data_dict[ip] = {}

# read tcp_log using BeautifulSoup
with open('./log/tcp_log.xml', 'r') as f:
    file = f.read()
data = BeautifulSoup(file, "xml")

## grab data from tcp_log file
host_list = data.find_all('host')
for host in host_list:
    try:    ### search for hostname base on ip address
        data_dict[host.find('address', {'addrtype': 'ipv4'}).get('addr')].update({'hostname': host.find('hostname').get('name')})
    except AttributeError:  ### if error: NONE TYPE, then insert 'None'
        data_dict[host.find('address', {'addrtype': 'ipv4'}).get('addr')].update({'hostname': 'None'})
    try:    ### search for mac_address base on ip address
        data_dict[host.find('address', {'addrtype': 'ipv4'}).get('addr')].update({'mac_address': host.find('address', {'addrtype': 'mac'}).get('addr')})
    except AttributeError:  ### if error: NONE TYPE, then insert 'None'
        data_dict[host.find('address', {'addrtype': 'ipv4'}).get('addr')].update({'mac_address': 'None'})
    try:    ### search for vendor base on ip address
        data_dict[host.find('address', {'addrtype': 'ipv4'}).get('addr')].update({'vendor': host.find('address', {'addrtype': 'mac'}).get('vendor')})
    except AttributeError:  ### if error: NONE TYPE, then insert 'None'
        data_dict[host.find('address', {'addrtype': 'ipv4'}).get('addr')].update({'vendor': 'None'})
    port_list = host.find_all('port')
    for port in port_list:  ### create tcp dictionary base on port id and insert protocol, status and service name
        data_dict[host.find('address', {'addrtype': 'ipv4'}).get('addr')].update({'port:'+port.get('portid'): {'protocol': port.get('protocol'), 'status': port.find('state').get('state'), 'service': port.find('service').get('name')}})

# read udp_log using BeautifulSoap
with open('./log/udp_log.xml', 'r') as f:
    file = f.read()
data = BeautifulSoup(file, "xml")

## grab data from udp_log file
host_list = data.find_all('host')
for host in host_list:
    port_list = host.find_all('port')
    for port in port_list:  ### create udp dictionary base on port id and insert protocol, status and service name
        data_dict[host.find('address', {'addrtype': 'ipv4'}).get('addr')].update({'port:'+port.get('portid'): {'protocol': port.get('protocol'), 'status': port.find('state').get('state'), 'service': port.find('service').get('name')}})   



print(data_dict)