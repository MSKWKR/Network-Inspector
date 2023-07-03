#!usr/bin/env python

from bs4 import BeautifulSoup
import pprint

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

class Data_dict:
    ## read log file using BeautifulSoup
    def __init__(self, log_type):
        self.log_type = log_type
        with open('./log/'+log_type+'_log.xml', 'r') as f:
            file = f.read()
        self.data = BeautifulSoup(file, "xml")
    ## define dictionary path
    def dict(self):
        return data_dict[host.find('address', {'addrtype': 'ipv4'}).get('addr')]

# grab data from tcp_log file
tcp = Data_dict("tcp")
host_list = tcp.data.find_all('host')
for host in host_list:
    try:    ### search for hostname base on ip address
        tcp.dict().update({'hostname': host.find('hostname').get('name')})
    except AttributeError:  ### if error: NONE TYPE, then insert 'None'
        tcp.dict().update({'hostname': 'None'})
    try:    ### search for mac_address base on ip address
        tcp.dict().update({'mac_address': host.find('address', {'addrtype': 'mac'}).get('addr')})
    except AttributeError:  ### if error: NONE TYPE, then insert 'None'
        tcp.dict().update({'mac_address': 'None'})
    try:    ### search for vendor base on ip address
        tcp.dict().update({'vendor': host.find('address', {'addrtype': 'mac'}).get('vendor')})
    except AttributeError:  ### if error: NONE TYPE, then insert 'None'
        tcp.dict().update({'vendor': 'None'})
    port_list = host.find_all('port')
    for port in port_list:  ### create tcp dictionary base on port id and insert protocol, status and service details
        tcp.dict().update({'port:'+port.get('portid'): {'protocol': port.get('protocol'), 'status': port.find('state').get('state'), 'service': port.find('service').get('name'), 'product': port.find('service').get('product'), 'service_fingerprint': port.find('service').get('servicefp'), 'os_type': port.find('service').get('ostype'), 'device_type': port.find('service').get('devicetype'), 'extra_info': port.find('service').get('extrainfo')}})

# grab data from udp_log file
udp = Data_dict("udp")
host_list = udp.data.find_all('host')
for host in host_list:
    port_list = host.find_all('port')
    for port in port_list:  ### create udp dictionary base on port id and insert protocol, status and service name
        udp.dict().update({'port:'+port.get('portid'): {'protocol': port.get('protocol'), 'status': port.find('state').get('state'), 'service': port.find('service').get('name'), 'product': port.find('service').get('product'), 'service_fingerprint': port.find('service').get('servicefp'), 'os_type': port.find('service').get('ostype'), 'device_type': port.find('service').get('devicetype'), 'extra_info': port.find('service').get('extrainfo')}})   

# grab highest OS probability
os = Data_dict("os")
host_list = os.data.find_all('host')
for host in host_list:
    try:
        os.dict().update({'operating_system': host.find('osmatch').get('name')})
    except AttributeError:
        os.dict().update({'operating_system': 'None'})

pprint.pprint(data_dict)