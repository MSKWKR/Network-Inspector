#!usr/bin/env python

"""log_parser.py parses the log files that scanner.sh produced into a JSON file.

Files Needed:

    lists/ip_list.txt
    log/tcp_log.xml
    log/udp_log.xml
    log/snmp_log.xml
    log/dhcp_log.xml
    log/dns_log.xml

How To Use: 

    from log_parser.py import InvManager
    InvManager.export(/PATH/TO/FILE) 
"""

"""BeautifulSoup is the main tool for parsing the xml files, datetime is used for naming and identifying the JSON files."""
from bs4 import BeautifulSoup
import json
from datetime import datetime

"""This class regulates all operations regarding unproccessed files."""
class FileChecker:
    """Checks whether the file exists or contains information for the script to run."""
    def __init__(self, file_name: str, file_type: str):
        """
        if a FileNotFoundError pops up during process then print error message and exit:
            if the file type is "log":
                open and read data from the file
                check data for the word "nmaprun" to ensure file contains info
                if not then print error message and exit the script

            else if the file type is "list":
                open and list data from the file
                if the list is empty then print error message and exit the script
        """
        try:
            if file_type == "log":
                with open('./log/'+file_name+'_log.xml', 'r') as f:
                    file = f.read()
                data = BeautifulSoup(file, "xml")
                if len(data.find("nmaprun")) == 0:
                    print("Error: Empty log file.")
                    exit()
                self.data = data

            elif file_type == "list":
                with open('./lists/'+file_name+'_list.txt', 'r') as f:
                    ip_list = f.readlines()
                if len(ip_list) == 0:
                    print("Error: Empty list file.")
                    exit()
                self.ip_list = ip_list
                
        except FileNotFoundError:
            print("Error: Missing "+file_name+file_type+" file.")
            exit()

    """This function returns a list of hosts from data."""
    def get_host(self) -> list:
        return self.data.find_all("host")


"""This class recieves data directly from InvManager then process it into the desired format."""
class Parser:
    """This function finds address from data based on address type and returns the string."""
    def find_address(self, host: str, type: str) -> str | None:
        if host.find('address', {'addrtype': type}):
            return host.find('address', {'addrtype': type}).get('addr')
        return None

    """This function finds the vendor from data based on mac address and returns the string."""
    def find_vendor(self, host: str) -> str | None:
        if host.find('address', {'addrtype': 'mac'}):
            return host.find('address', {'addrtype': 'mac'}).get('vendor')
        return None

    """This function finds the hostname from data and returns the string."""
    def find_host_name(self, host: str) -> str | None:
        if host.find('hostname'):
            return host.find('hostname').get('name')
        return None

    """This function finds ports with discriptions, formats it then returns a list"""
    def find_ports(self, host: str) -> list | None:
        """
        if there are information about ports in data:
            create a list containing all port data: "port_list"
            create a list of dictionaries which stores properties of each port: "port_info_list"
            for every port in port_list create a dictionary for each port property and store it in "port_dict"
                append port_dict into port_info_list
            return port_info_list
        """
        if host.find_all('port'):
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
        return None

    """This function finds dhcp server ip and router ip from data, then retuns the string."""  
    def find_dhcp(self, host: str, type: str) -> str | None:
        if host.find('script'):
            if type == "dhcp":
                return host.find('script').find('elem', {'key': 'Server Identifier'}).string
            elif type == "router":
                return host.find('script').find('elem', {'key': 'Router'}).string
        return None

    """This function finds information on snmp ports based on type, then returns a dictionary.""" 
    def find_snmp(self, host: str, type: str) -> dict | None:
        """if the nmap script ran properly then proceed"""
        if host.find('script', {'id': type}):
            """
            if type is snmp-sysdescr:
                split string for system name and system uptime
                insert into snmp_dict and return the dictionary

            else if type is snmp-info then find boot cycle and return dictionary

            else if type is snmp-interfaces:
                create a dictionary to store all interfaces: "interface_dict"
                store interface details as dictionaries in interface_dict
                return interface_dict

            else if type is snmp-processes:
                create dictionary to store all processes: "process_dict"
                store all properties of the process in process_dict
                return process_dict 

            else if type is snmp-win32-software:
                create dictionary to store all software: "software_dict"
                store all properties of the software in software_dict
                return software_dict 
            """
            if type == "snmp-sysdescr":
                system_name = host.find('script', {'id': 'snmp-sysdescr'}).get('output').split('\n')[0]
                system_uptime = host.find('script', {'id': 'snmp-sysdescr'}).get('output').split('\n')[1].split('System uptime:')[1].strip()
                snmp_dict = {
                    'system_name': system_name,
                    'system_uptime': system_uptime
                }
                return snmp_dict
            
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
                The parameter "len(device_list)-1" indicates the position of the device in device_list is one position lower than the length of device_list.
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
        return None

    """This function finds dns caches and details of services from data then returns a dictionary."""
    def find_dns(self, data: str, type: str) -> dict | None:
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
        return None

"""This class receives data from FileChecker, sends it to Parser, receives parsed data from Parser, then appends the data to inventory."""
class InvManager:
    """Create net_inv which is the inventory for all processed data"""
    def __init__(self):
        """
        check for the existence of ip_list:
            create a dictionary for every ip address in ip_list
            create a dictionary called "ports" in every ip dictionary
        create an instance for the Parser class
        """
        check = FileChecker("ip", "list")
        net_inv = {}
        for ip in check.ip_list:
            net_inv.update({ip.strip(): {}})
            net_inv[ip.strip()].update({'ports': {}})
        self.net_inv = net_inv
        parse = Parser()
        self.parse = parse

    """This function adds hostname, mac address and vendor to inventory."""
    def basic_parser(self) -> None:
        """
        get a list of hosts from FileChecker
        for every host check if ip address exists in inventory:
            if ip exists then search for hostname, mac address, vendor and add them to inventory
        """
        check = FileChecker("tcp", "log")
        for host in check.get_host():
            ip_address = self.parse.find_address(host, "ipv4")
            if ip_address in self.net_inv:
                self.net_inv[ip_address].update({'mac_address': self.parse.find_address(host, "mac")})
                self.net_inv[ip_address].update({'vendor': self.parse.find_vendor(host)})
                self.net_inv[ip_address].update({'hostname': self.parse.find_host_name(host)})

    """This function adds detailed information for every tcp port in inventory."""
    def tcp_parser(self) -> None:
        """
        get a list of hosts from FileChecker
        for every host check if ip address exists in inventory:
            for every ip check if there are information about ports
                if port exists then create a dictionary for every port and add information
        """
        check = FileChecker("tcp", "log")
        for host in check.get_host():
            ip_address = self.parse.find_address(host, "ipv4")
            if ip_address in self.net_inv:
                if self.parse.find_ports(host):
                    for port_dict in self.parse.find_ports(host):
                        self.net_inv[ip_address]['ports'].update(port_dict)

    """This function adds detailed information for every udp port in inventory."""
    def udp_parser(self) -> None:
        """
        get a list of hosts from FileChecker
        for every host check if ip address exists in inventory:
            for every ip check if there are information about ports
                if port exists then create a dictionary for every port and add information
        """
        check = FileChecker("udp", "log")
        for host in check.get_host():
            ip_address = self.parse.find_address(host, "ipv4")
            if ip_address in self.net_inv:
                if self.parse.find_ports(host):
                    for port_dict in self.parse.find_ports(host):
                        self.net_inv[ip_address]['ports'].update(port_dict)

    """This function runs tcp and udp parser then checks for empty "ports" dictionary in inventory."""
    def port_parser(self) -> None:
        """
        run tcp_parser and udp_parser
        for every ip in inventory:
            check if "ports" dictionary is empty:
                if empty then change "ports" value to None
        """
        self.tcp_parser()
        self.udp_parser()
        for ip in self.net_inv:
            if self.net_inv[ip]['ports']:
                    pass
            else:
                self.net_inv[ip].update({'ports': None})

    """This function adds dhcp server ip and router ip to inventory."""
    def dhcp_parser(self) -> None:
        """
        get a list of hosts from FileChecker
        if host data contains dhcp server ip and router ip
            add the information to inventory
        """
        check = FileChecker("dhcp", "log")
        for host in check.get_host():
            self.net_inv.update({'dhcp_server': self.parse.find_dhcp(host, "dhcp")})
            self.net_inv.update({'router_ip': self.parse.find_dhcp(host, "router")})

    """This function adds detailed snmp info to hosts that enable the snmp port."""  
    def snmp_parser(self) -> None:
        """
        get a list of hosts from FileChecker
        for every host check if ip address exists in inventory:
            for every ip create dictionary called "snmp_info":
                check if the type of info exists:
                    if exist then add details to "snmp_info"
        """
        check = FileChecker("snmp", "log")
        for host in check.get_host():
            ip_address = self.parse.find_address(host, "ipv4")
            if ip_address in self.net_inv:
                self.net_inv[ip_address].update({'snmp_info': {}})
                if self.parse.find_snmp(host, "snmp-sysdescr"):
                    self.net_inv[ip_address]['snmp_info'].update(self.parse.find_snmp(host, "snmp-sysdescr"))
                if self.parse.find_snmp(host, "snmp-info"):
                    self.net_inv[ip_address]['snmp_info'].update(self.parse.find_snmp(host, "snmp-info"))
                if self.parse.find_snmp(host, "snmp-interfaces"):
                    self.net_inv[ip_address]['snmp_info'].update({'interfaces': self.parse.find_snmp(host, "snmp-interfaces")})
                if self.parse.find_snmp(host, "snmp-processes"):
                    self.net_inv[ip_address]['snmp_info'].update({'processes': self.parse.find_snmp(host, "snmp-processes")})
                if self.parse.find_snmp(host, "snmp-win32-software"):
                    self.net_inv[ip_address]['snmp_info'].update({'softwares': self.parse.find_snmp(host, "snmp-win32-software")})
                if self.net_inv[ip_address]['snmp_info']:
                    pass
                else:
                    self.net_inv[ip_address].update({'snmp_info': None})

    """This function uses info from dns_log to update inventory infos that are empty, and add results of dns cache snoop to inventory."""
    def dns_parser(self) -> None:
        check = FileChecker("dns", "log")
        """
        create a dictionary in inventory for "dns_cache"
        for every dns host create a dictionary:
            add the cache into the dictionary
        """
        self.net_inv.update({'dns_cache': {}})
        for host in check.get_host():
            if self.parse.find_dns(host, "cache"):
                self.net_inv['dns_cache'].update(self.parse.find_dns(host, "cache"))

        """
        check if there is data in broadcast-dns-service-discovery:
            if there is data and ip exists in inventory:
                check if port exists in inventory:
                    if exist then update the "state" to "up"
                    if there is info about the service of the port then add it in
                    if there are other infos then add it to extra info
                else if port doesn't exist in inventory:
                    create a dictionary for the port and add "state", "service" and "extra_info"
        """
        if self.parse.find_dns(check.data, "service"):
            dns_dict = self.parse.find_dns(check.data, "service")
            for ip in dns_dict:
                if ip in self.net_inv:
                        for port in dns_dict[ip]:
                            if self.net_inv[ip]['ports']:
                                if port in self.net_inv[ip]['ports']:
                                    state = self.net_inv[ip]['ports'][port]['state']
                                    if state == "closed" or state == "closed|filtered" or state == "open|filtered" or state == "filtered":
                                         self.net_inv[ip]['ports'][port]['state'] = "open"
                                    if self.net_inv[ip]['ports'][port]['service'] == None:
                                        self.net_inv[ip]['ports'][port]['service'] = dns_dict[ip][port]["service"]
                                    if self.net_inv[ip]['ports'][port]['extra_info'] == None:
                                        if dns_dict[ip][port]["extra_info"]:
                                            self.net_inv[ip]['ports'][port]['extra_info'] = dns_dict[ip][port]["extra_info"]
                                else:
                                    self.net_inv[ip]['ports'].update({port: dns_dict[ip][port]})
                            else:
                                self.net_inv[ip]['ports']= {port: dns_dict[ip][port]}

    """This function runs the entire script then exports a JSON of the inventory."""
    def export(self, file_path: str, folder: str = "") -> None:
        self.basic_parser()
        self.port_parser()
        self.dhcp_parser()
        self.snmp_parser()
        self.dns_parser()
        """if folder is specified then export into the folder"""
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
    """JSON file is named after time, so there will be no duplicates"""
    time_of_creation = now.strftime("%Y_%b_%d_%H_%M")
    run.export(time_of_creation)
    

if __name__ == "__main__":
    main()