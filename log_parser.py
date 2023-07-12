#!usr/bin/env python

from bs4 import BeautifulSoup
import json
from datetime import datetime

# Check if file exists
def file_checker(file_name: str, file_type:str) -> None:
    try:
        if file_type == "log":
            with open('./log/'+file_name+'_log.xml', 'r') as f:
                file = f.read()
            data = BeautifulSoup(file, "xml")
            host_list = list(data.find_all('host'))
            # Check if log is empty
            if len(host_list) == 0:
                print("Error: Empty log file.")
                exit()
        elif file_type == "list":
            with open('./lists/'+file_name+'_list.txt', 'r') as f:
                file_list = f.readlines()
            # Check if list is empty
            if len(file_list) == 0:
                print("Error: Empty list file.")
                exit()
    except FileNotFoundError:
        print("Error: Missing "+file_name+file_type+" file.")
        exit()

class Parser:
    # File check and pull host tag from log file
    def __init__(self, log_type: str) -> None:
        self.log_type = log_type
        file_checker(log_type, "log")
        with open('./log/'+log_type+'_log.xml', 'r') as f:
            file = f.read()
        data = BeautifulSoup(file, "xml")
        self.host_list = data.find_all('host')
        self.data = data

    # Find ip and mac from host tag
    def find_address(self, host: str, type: str) -> str:
        if host.find('address', {'addrtype': type}):
            return host.find('address', {'addrtype': type}).get('addr')
        else:
            return None

    # Find vendor from mac address
    def find_vendor(self, host: str) -> str:
        if host.find('address', {'addrtype': 'mac'}):
            return host.find('address', {'addrtype': 'mac'}).get('vendor')
        else:
            return None

    # Find hostname of the host
    def find_host_name(self, host: str) -> str:
        if host.find('hostname'):
            return host.find('hostname').get('name')
        else:
            return None

    # Find port information in host tag, return dictionary list
    def find_ports(self, host: str) -> list:
        if host.find_all('port'):
            # Create dictionary for each port id
            port_list = host.find_all('port')
            port_info_list = []
            for port in port_list:
                port_id = port.get('portid')
                port_protocol = port.get('protocol')
                port_state = port.find('state').get('state')
                port_service = port.find('service').get('name')
                service_product = port.find('service').get('product')
                service_type = port.find('service').get('devicetype')
                service_fingerprint = port.find('service').get('servicefp')
                os_type = port.find('service').get('ostype')
                extra_info = port.find('service').get('extrainfo')
                port_dict = {
                    'protocol': port_protocol, 
                    'state': port_state, 
                    'service': port_service, 
                    'product': service_product, 
                    'service_type': service_type, 
                    'service_fingerprint': service_fingerprint,
                    'os_type': os_type,
                    'extra_info': extra_info
                    }
                port_info_list.append({port_id: port_dict})
            return port_info_list
        else:
            return None

    # Find dhcp server and router ip   
    def find_dhcp(self, host: str, type: str) -> str:
        if host.find('script'):
            if type == "dhcp":
                return host.find('script').find('elem', {'key': 'Server Identifier'}).string
            elif type == "router":
                return host.find('script').find('elem', {'key': 'Router'}).string
        else:
            return None

    # Pull all snmp information, return dictionary for every major type of query  
    def find_snmp(self, host: str, type: str) -> dict:
        # Check for script tag
        if host.find('script', {'id': type}):
            # Info from --script=snmp-sysdescr
            if type == "snmp-sysdescr":
                system_name = host.find('script', {'id': 'snmp-sysdescr'}).get('output').split('\n')[0]
                system_uptime = host.find('script', {'id': 'snmp-sysdescr'}).get('output').split('\n')[1].split('System uptime:')[1].strip()
                snmp_dict = {
                    'system_name': system_name,
                    'system_uptime': system_uptime
                }
                return snmp_dict
            
            # Info from --script=snmp-info
            elif type == "snmp-info":
                boot_cycle = host.find('script', {'id': 'snmp-info'}).find('elem', {'key': 'snmpEngineBoots'}).string
                return {'boot_cycle': boot_cycle}
            
            # Info from --script=snmp-interfaces
            elif type == "snmp-interfaces":
                interface_list = list(host.find('script', {'id': 'snmp-interfaces'}).get('output').split("\n"))
                interface_list = [x for x in interface_list if x]   # Remove empty strings from list
                device_list = [(interface_list[0].lstrip())]    # Device list stores name of devices/interfaces
                ''' 
                Create dictionary for each device/interface.
                The parameter "len(device_list)-1" indicates the position of the device in device_list is one position lower than the length of device_list 
                '''
                interface_dict = {device_list[len(device_list)-1]: {}}
                for interface in interface_list:
                    # Ignore the first entry, as it is the name of the device
                    if device_list[len(device_list)-1] in interface:
                        pass
                    # Grab ipv4 address and network mask of the device
                    elif "IP address" in interface:
                        interface_dict[device_list[len(device_list)-1]].update({'ip': interface.split("IP address:")[1].split("Netmask")[0].strip()})
                        interface_dict[device_list[len(device_list)-1]].update({'mask': interface.split("Netmask:")[1].strip()})
                    # Grab mac address and vendor of the device
                    elif "MAC address" in interface:
                        interface_dict[device_list[len(device_list)-1]].update({'mac': interface.split("MAC address:")[1].strip().split()[0]})
                        interface_dict[device_list[len(device_list)-1]].update({'vendor': interface.split("MAC address:")[1].strip().split()[1].strip("()")})
                    # Grab device type and transmission speed of the device    
                    elif "Type" in interface:
                        interface_dict[device_list[len(device_list)-1]].update({'device_type': interface.split("Type:")[1].split("Speed:")[0].strip()})
                        interface_dict[device_list[len(device_list)-1]].update({'device_speed': interface.split("Type:")[1].split("Speed:")[1].lstrip()})
                    # Grab the status of the device    
                    elif "Status" in interface:
                        interface_dict[device_list[len(device_list)-1]].update({'device_status': interface.split("Status:")[1].strip()})
                    # Grab amount of data sent and received by device    
                    elif "Traffic stats" in interface:
                        interface_dict[device_list[len(device_list)-1]].update({'sent': interface.split("Traffic stats:")[1].split("sent")[0].strip()})
                        interface_dict[device_list[len(device_list)-1]].update({'received': interface.split("sent,")[1].split("received")[0].strip()})
                    else:
                        # If the data type is unrecognized then it might be a new device, add the new device name to device_list
                        device_list.append(interface.lstrip())
                        interface_dict.update({device_list[len(device_list)-1]: {}})
                return interface_dict
        
            # Info from --script=snmp-processes
            elif type == "snmp-processes":
                process_list = host.find('script', {'id': 'snmp-processes'}).find_all('table')
                process_dict = {}
                # Create dictionary for every process key/id
                for process in process_list:
                    process_dict.update({process.get('key'): {}})
                    # Grab name of the process
                    if process.find('elem', {'key': 'Name'}):
                        process_dict[process.get('key')].update({'name': process.find('elem', {'key': 'Name'}).string})
                    # Grab path of the process
                    if process.find('elem', {'key': 'Path'}):
                        process_dict[process.get('key')].update({'path': process.find('elem', {'key': 'Path'}).string})
                    # Grab parameters for the process
                    if process.find('elem', {'key': 'Params'}):
                        process_dict[process.get('key')].update({'parameters': process.find('elem', {'key': 'Params'}).string})
                return process_dict
            
            # Info from --script=snmp-win32-software
            elif type == "snmp-win32-software":
                software_list = host.find('script', {'id': 'snmp-win32-software'}).find_all('table')
                software_dict = {}
                # Create dictionary for every software
                for software in software_list:
                    # Grab name of software
                    software_dict.update({software.find('elem', {'key': 'name'}).string.split(',')[1]: {}})
                    # Grab the vendor of the software
                    software_dict[software.find('elem', {'key': 'name'}).string.split(',')[1]].update({'vendor': software.find('elem', {'key': 'name'}).string.split(',')[0]})
                    # Grab the version of the software
                    software_dict[software.find('elem', {'key': 'name'}).string.split(',')[1]].update({'version': software.find('elem', {'key': 'name'}).string.split(',')[2]})
                    # Grab the installation date of the software
                    software_dict[software.find('elem', {'key': 'name'}).string.split(',')[1]].update({'install_date': software.find('elem', {'key': 'install_date'}).string})
                return software_dict
        else:
            return None

    # Pull dns cache and services
    def find_dns(self, data: str, type: str) -> dict:
        # Pull cache from -script=dns-cache-snoop.nse
        if type == "cache":
            if data.find('script', {'id': 'dns-cache-snoop'}):
                cache = data.find('script', {'id': 'dns-cache-snoop'}).get('output').split("\n")
                del cache[0]    # Remove header
                return {self.find_address(data, "ipv4"): cache}

        # Using dns service discovery to pull information about services that are usually hidden
        elif type == "service":
            if data.find('prescript'):
                service_dict = {}
                extra_info = []
                service_list = data.find('script', {'id': 'broadcast-dns-service-discovery'}).get('output').strip().split("\n")
                del service_list[0] # First entry of the output is mdns ip
                # Parse out port id, protocol and service type
                for text in service_list:
                    if "tcp" in text or "udp" in text:
                        port = text.split("/")[0].strip()
                        protocol = text.split("/")[1].split()[0]
                        service = text.split("/")[1].split()[1]
                    elif "Address" in text:
                        ip = text.split("=")[1].split()[0]
                        if extra_info:
                            pass
                        else:
                            extra_info = None
                        # Create dictionary for every port with the format similar to find_port()
                        port_dict = {
                            'protocol': protocol,
                            'state': "open",
                            'service': service,
                            'extra_info': extra_info
                        }
                        # Create dictionary for every ip in service list
                        ip_dict = {port: port_dict}
                        if ip in service_dict:
                            service_dict[ip].update(ip_dict)
                        else:
                            service_dict.update({ip: ip_dict})
                        extra_info = []
                    else:
                        extra_info.append(text.strip())
                return service_dict

class InvManager:
    def __init__(self) -> None:
        # Create dictionary template
        file_checker("ip", "list")
        net_inv = {}
        with open('./lists/ip_list.txt', 'r') as f:
            ip_list = f.readlines()
        # Every ip address is a dictionary
        for ip in ip_list:
            net_inv.update({ip.strip(): {}})
            net_inv[ip.strip()].update({'ports': {}})
        self.net_inv = net_inv

    # Add mac address, vendor and hostname to dictionary
    def basic_parser(self) -> None:
        parse = Parser("tcp")
        for host in parse.host_list:
            ip_address = parse.find_address(host, "ipv4")
            if ip_address in self.net_inv:
                self.net_inv[ip_address].update({'mac_address': parse.find_address(host, "mac")})
                self.net_inv[ip_address].update({'vendor': parse.find_vendor(host)})
                self.net_inv[ip_address].update({'hostname': parse.find_host_name(host)})

    # Add tcp port information
    def tcp_parser(self) -> None:
        parse = Parser("tcp")
        for host in parse.host_list:
            ip_address = parse.find_address(host, "ipv4")
            if ip_address in self.net_inv:
                if parse.find_ports(host):
                    for port_dict in parse.find_ports(host):
                        self.net_inv[ip_address]['ports'].update(port_dict)

    # Add udp port information
    def udp_parser(self) -> None:
        parse = Parser("udp")
        for host in parse.host_list:
            ip_address = parse.find_address(host, "ipv4")
            if ip_address in self.net_inv:
                if parse.find_ports(host):
                    for port_dict in parse.find_ports(host):
                        self.net_inv[ip_address]['ports'].update(port_dict)

    # Check results of tcp_parser and udp_parser
    def port_parser(self) -> None:
        self.tcp_parser()
        self.udp_parser()
        parse = Parser("tcp")
        for host in parse.host_list:
            ip_address = parse.find_address(host, "ipv4")
            if ip_address in self.net_inv:
                if self.net_inv[ip_address]['ports']:
                    pass
                else:
                    self.net_inv[ip_address].update({'ports': None})

    # Add dhcp server ip and router ip
    def dhcp_parser(self) -> None:
        parse = Parser("dhcp")
        for host in parse.host_list:
            ip_address = parse.find_address(host, "ipv4")
            if ip_address in self.net_inv:
                self.net_inv[ip_address].update({'dhcp_server': parse.find_dhcp(host, "dhcp")})
                self.net_inv[ip_address].update({'router_ip': parse.find_dhcp(host, "router")})
            else:
                self.net_inv.update({'dhcp_server': parse.find_dhcp(host, "dhcp")})
                self.net_inv.update({'router_ip': parse.find_dhcp(host, "router")})

    # Add snmp information to dictionary   
    def snmp_parser(self) -> None:
        parse = Parser("snmp")
        for host in parse.host_list:
            ip_address = parse.find_address(host, "ipv4")
            if ip_address in self.net_inv:
                self.net_inv[ip_address].update({'snmp_info': {}})
                if parse.find_snmp(host, "snmp-sysdescr"):
                    self.net_inv[ip_address]['snmp_info'].update(parse.find_snmp(host, "snmp-sysdescr"))
                if parse.find_snmp(host, "snmp-info"):
                    self.net_inv[ip_address]['snmp_info'].update(parse.find_snmp(host, "snmp-info"))
                if parse.find_snmp(host, "snmp-interfaces"):
                    self.net_inv[ip_address]['snmp_info'].update({'interfaces': parse.find_snmp(host, "snmp-interfaces")})
                if parse.find_snmp(host, "snmp-processes"):
                    self.net_inv[ip_address]['snmp_info'].update({'processes': parse.find_snmp(host, "snmp-processes")})
                if parse.find_snmp(host, "snmp-win32-software"):
                    self.net_inv[ip_address]['snmp_info'].update({'softwares': parse.find_snmp(host, "snmp-win32-software")})
                if self.net_inv[ip_address]['snmp_info']:
                    pass
                else:
                    self.net_inv[ip_address].update({'snmp_info': None})

    # Add dns cache to dictionary and update port information based on service discovery
    def dns_parser(self) -> None:
        parse = Parser("dns")
        # Add a dictionary for dns cache domains
        self.net_inv.update({'dns_cache': {}})
        for host in parse.host_list:
            if parse.find_dns(host, "cache"):
                # Create dictionary for each dns server
                self.net_inv['dns_cache'].update(parse.find_dns(host, "cache"))
        # Update the port dictionary
        if parse.find_dns(parse.data, "service"):
            dns_dict = parse.find_dns(parse.data, "service")
            for ip in dns_dict:
                if ip in self.net_inv:
                        for port in dns_dict[ip]:
                            if self.net_inv[ip]['ports']:
                                if port in self.net_inv[ip]['ports']:
                                    state = self.net_inv[ip]['ports'][port]['state']
                                    # If port is found in dns services, then the port is open
                                    if state == "closed" or state == "closed|filtered" or state == "open|filtered" or state == "filtered":
                                         self.net_inv[ip]['ports'][port]['state'] = "open"
                                    # If service name is found in dns services then update net_inv
                                    if self.net_inv[ip]['ports'][port]['service'] == None:
                                        self.net_inv[ip]['ports'][port]['service'] = dns_dict[ip][port]["service"]
                                    if self.net_inv[ip]['ports'][port]['extra_info'] == None:
                                        if dns_dict[ip][port]["extra_info"]:
                                            self.net_inv[ip]['ports'][port]['extra_info'] = dns_dict[ip][port]["extra_info"]
                                # If the port is not found in net_inv, then create a dictionary for the port and format it to have basic information
                                else:
                                    self.net_inv[ip]['ports'].update({port: dns_dict[ip][port]})
                            else:
                                self.net_inv[ip]['ports']= {port: dns_dict[ip][port]}

    # Run entire script then export the dictionary into a json file
    def export(self, file_path: str, folder="") -> None:
        self.basic_parser()
        self.port_parser()
        self.dhcp_parser()
        self.snmp_parser()
        self.dns_parser()
        if folder:
            with open(folder+"/"+file_path+".json", "w") as file:
                json.dump(self.net_inv, file, indent=4)
        else:
            with open(file_path+".json", "w") as file:
                json.dump(self.net_inv, file, indent=4)
        print("Status: JSON file created successfully.")


def main():
    run = InvManager()
    now = datetime.now()
    time_of_creation = now.strftime("%Y_%b_%d_%H_%M")
    run.export(time_of_creation)
    

if __name__ == "__main__":
    main()