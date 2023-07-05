#!usr/bin/env python

from bs4 import BeautifulSoup
import json

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

# initialize BeautifulSoup to parse xml
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
host_list = tcp.data.find_all('host')   ## each host tag contains all information
for host in host_list:
    try:    ## search for hostname base on ip address
        tcp.dict().update({'hostname': host.find('hostname').get('name')})
    except AttributeError:  ## if error: NONE TYPE, then insert 'None'
        tcp.dict().update({'hostname': None})
    try:    ## search for mac_address base on ip address
        tcp.dict().update({'mac_address': host.find('address', {'addrtype': 'mac'}).get('addr')})
    except AttributeError:  ## if error: NONE TYPE, then insert 'None'
        tcp.dict().update({'mac_address': None})
    try:    ## search for vendor base on ip address
        tcp.dict().update({'vendor': host.find('address', {'addrtype': 'mac'}).get('vendor')})
    except AttributeError:  ## if error: NONE TYPE, then insert 'None'
        tcp.dict().update({'vendor': None})
    ## port_list stores all port related information
    port_list = host.find_all('port')
    for port in port_list:  ## create tcp dictionary base on port id and insert protocol, status and service name
        tcp.dict().update({'port:'+port.get('portid'): {'protocol': port.get('protocol'), 'status': port.find('state').get('state'), 'service': port.find('service').get('name')}})
        ## service details: product_name, service_fingerprint, os_type, device_type and extra_info
        tcp.dict()['port:'+port.get('portid')].update({'product': port.find('service').get('product'), 'service_fingerprint': port.find('service').get('servicefp'), 'os_type': port.find('service').get('ostype'), 'device_type': port.find('service').get('devicetype'), 'extra_info': port.find('service').get('extrainfo')})

# grab data from udp_log file
udp = Data_dict("udp")
host_list = udp.data.find_all('host')   ## each host tag contains all information
for host in host_list:
    ## port_list stores all port related information
    port_list = host.find_all('port')
    for port in port_list:  ## create udp dictionary base on port id and insert protocol, status and service name
        udp.dict().update({'port:'+port.get('portid'): {'protocol': port.get('protocol'), 'status': port.find('state').get('state'), 'service': port.find('service').get('name')}})
        ## service details: product_name, service_fingerprint, os_type, device_type and extra_info
        udp.dict()['port:'+port.get('portid')].update({'product': port.find('service').get('product'), 'service_fingerprint': port.find('service').get('servicefp'), 'os_type': port.find('service').get('ostype'), 'device_type': port.find('service').get('devicetype'), 'extra_info': port.find('service').get('extrainfo')})

# tag dhcp server and router ip
dhcp = Data_dict("dhcp")
host_list = dhcp.data.find_all('host')
for host in host_list:
    try:
        dhcp.dict().update({'dhcp_server': host.find('script').find('elem', {'key': 'Server Identifier'}).string})
        dhcp.dict().update({'router': host.find('script').find('elem', {'key': 'Router'}).string})
    except AttributeError:
        pass 

# grab highest OS probability
os = Data_dict("os")
host_list = os.data.find_all('host')   ## each host tag contains all information
for host in host_list:
    try:    ## search for highest os probability base on ip address
        os.dict().update({'operating_system': host.find('osmatch').get('name')})
    except AttributeError:  ## if error: NONE TYPE, then insert 'None'
        os.dict().update({'operating_system': None})

# grab data from snmp_log file:
snmp = Data_dict("snmp")
host_list = snmp.data.find_all('host')   ## each host tag contains all information
for host in host_list:
    ## grab snmp system description
    try:
        snmp.dict().update({'snmp_system_description': {'system_name': host.find('script', {'id': 'snmp-sysdescr'}).get('output').split('\n')[0]}})
        snmp.dict()['snmp_system_description'].update({'system_uptime': host.find('script', {'id': 'snmp-sysdescr'}).get('output').split('\n')[1].split('System uptime:')[1].strip()})
    except AttributeError:  ## if error: NONE TYPE, then insert 'None'
        snmp.dict().update({'snmp_system_description': None})

    ## grab snmp info
    info_list = []
    try:
        info_list = host.find('script', {'id': 'snmp-info'}).get('output').split("\n")   ## insert entire snmp-info script output to info_list
        snmp.dict().update({'snmp_info': {}})
    except AttributeError:  ## if error: NONE TYPE, then insert 'None'
        snmp.dict().update({'snmp_info': None})
    for info in info_list:
        if "enterprise" in info:
            snmp.dict()['snmp_info'].update({'enterprise': info.split("enterprise: ")[1]})
        elif "engineIDFormat:" in info:
            snmp.dict()['snmp_info'].update({'id_format': info.split("engineIDFormat: ")[1]})
        elif "engineIDData:" in info:
            snmp.dict()['snmp_info'].update({'id_data': info.split("engineIDData: ")[1]})
        elif "snmpEngineBoots:" in info:
            snmp.dict()['snmp_info'].update({'boot_count': info.split("snmpEngineBoots: ")[1]})
        else:
            pass

    ## check snmp processes
    process_list = []
    snmp.dict().update({'snmp_process': {}})
    ## process information are stored in tables
    try:
        process_list = host.find('script', {'id': 'snmp-processes'}).find_all('table')
    except AttributeError:  ## if error: NONE TYPE, then insert 'None'
            snmp.dict().update({'snmp_process': None})    
    for process in process_list:
        ## create a dictionary for every key
        snmp.dict()['snmp_process'].update({process.get('key'): {}})
        try:
            ## process name
            snmp.dict()['snmp_process'][process.get('key')].update({"type": process.find('elem', {'key': 'Name'}).string})
        except AttributeError:  ## if error: NONE TYPE, then insert 'None'
            snmp.dict()['snmp_process'][process.get('key')].update({"type": None})
        try:
            ## process path
            snmp.dict()['snmp_process'][process.get('key')].update({"path": process.find('elem', {'key': 'Path'}).string})
        except AttributeError:  ## if error: NONE TYPE, then insert 'None'
            snmp.dict()['snmp_process'][process.get('key')].update({"path": None})
        try:
            ## process parameters
            snmp.dict()['snmp_process'][process.get('key')].update({"parameters": process.find('elem', {'key': 'Params'}).string})
        except AttributeError:  ## if error: NONE TYPE, then insert 'None'
            snmp.dict()['snmp_process'][process.get('key')].update({"parameters": None})
    
    ## check win32 softwares 
    software_list = []
    snmp.dict().update({'win32_software': {}})
    ## software information are stored in tables
    try:
        software_list = host.find('script', {'id': 'snmp-win32-software'}).find_all('table')
    except AttributeError:  ## if error: NONE TYPE, then insert 'None'
            snmp.dict().update({'win32_software': None})
    for software in software_list:
            ## create a dictionary for every software detected and add install_date
            snmp.dict()['win32_software'].update({software.find('elem', {'key': 'name'}).string: {'install_date': software.find('elem', {'key': 'install_date'}).string}})

    ## check snmp info
    ## create info_list to store entire snmp-interface script output
    interface_list = []
    ## create device_list to store every device in snmp_log
    device_list = []
    num = 0 ## keep a tab on how many devices
    try:
        interface_list = host.find('script', {'id': 'snmp-interfaces'}).get('output').split("\n")   ## insert entire snmp-interface script output to interface_list
        interface_list = [x for x in interface_list if x] ## remove empty strings in interface_list
        device_list.append(interface_list[0].lstrip())   ## insert first device from interface_list
        snmp.dict().update({'snmp_interface': {device_list[0]: {}}}) ## create dictionary to store details of the device
    except AttributeError:  ## if error: NONE TYPE, then insert 'None'
        snmp.dict().update({'snmp_interface': None})
    ## loop through interface_list to grab data
    for info in interface_list:
        ## pass if info is device name
        if device_list[num] in info:
            pass
        elif "IP address" in info:
            ## grab ipv4 address and network mask of the device
            snmp.dict()['snmp_interface'][device_list[num]].update({'ip': info.split("IP address:")[1].split("Netmask")[0].strip()})
            snmp.dict()['snmp_interface'][device_list[num]].update({'mask': info.split("Netmask:")[1].strip()})
        elif "MAC address" in info:
            ## grab mac address and vendor of the device
            snmp.dict()['snmp_interface'][device_list[num]].update({'mac': info.split("MAC address:")[1].strip().split()[0]})
            snmp.dict()['snmp_interface'][device_list[num]].update({'vendor': info.split("MAC address:")[1].strip().split()[1].strip("()")})
        elif "Type" in info:
            ## grab device type and transmission speed of the device
            snmp.dict()['snmp_interface'][device_list[num]].update({'type': info.split("Type:")[1].split("Speed:")[0].strip()})
            snmp.dict()['snmp_interface'][device_list[num]].update({'speed': info.split("Type:")[1].split("Speed:")[1].lstrip()})
        elif "Status" in info:
            ## grab the status of the device
            snmp.dict()['snmp_interface'][device_list[num]].update({'status': info.split("Status:")[1].strip()})
        elif "Traffic stats" in info:
            ## grab amount of data sent and received by device
            snmp.dict()['snmp_interface'][device_list[num]].update({'sent': info.split("Traffic stats:")[1].split("sent")[0].strip()})
            snmp.dict()['snmp_interface'][device_list[num]].update({'received': info.split("sent,")[1].split("received")[0].strip()})
        else:
            ## if the data type is unrecognized then it might be a new device name, add the new device name to device_list and create a dictionary for it 
            device_list.append(info.lstrip())
            num=num+1
            snmp.dict()['snmp_interface'].update({device_list[num]: {}})

# turn dictionary into json format
jsonify = json.dumps(data_dict, indent = 4)
print(jsonify)

# output results to database or api