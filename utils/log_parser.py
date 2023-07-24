#!usr/bin/env python

'''log_parser.py parses the log files that scanner.sh produced into a JSON file.'''

'''BeautifulSoup is the main tool for parsing the XML files, datetime is used for naming and identifying the JSON files.'''
from bs4 import BeautifulSoup
import json
from datetime import datetime


class FileChecker:
    """
        Regulates all operations regarding unproccessed files, mainly log files.
    """
    def __init__(self, file_name: str, file_type: str):
        """
            Checks whether the file exists or contains information for the script to run.
            
            :param file_name: Name of file
            :param file_type: Log or list
            :type: str 
        """
        try:
            if file_type == "log":
                with open('../../log/'+file_name+'_log.xml', 'r') as f:
                    file = f.read()
                data = BeautifulSoup(file, "xml")
                if data.find("nmaprun"):
                    if data.find("wireless-network"):
                        print("Error: Empty log file.")
                        exit()
                self.data = data

            elif file_type == "list":
                with open('../../lists/'+file_name+'_list.txt', 'r') as f:
                    ip_list = f.readlines()
                if len(ip_list) == 0:
                    print("Error: Empty list file.")
                    exit()
                self.ip_list = ip_list
                
        except FileNotFoundError:
            print("Error: Missing "+file_name+" "+file_type+" file.")
            exit()

    def get_host(self) -> list:
        """
            Returns a list of hosts from data.

            :return: A list of string with the host tag
            :rtype: list
        """
        return self.data.find_all("host")
    
    def get_wlan(self) -> list:
        """
            Returns a list of wireless-networks from data.

            :return: A list of string with the wireless-network tag
            :rtype: list
        """
        return self.data.find_all("wireless-network", {'type': 'infrastructure'})


class Parser:
    """
        Recieves data directly from InvManager then process it into the desired format.
    """
    def find_address(self, host: str, type: str) -> str | None:
        """
            Find address from host based on type and returns the string.

            :param host: The entire host tag string from the XML file
            :param type: Mac address or ipv4
            :type: str

            :return: Parsed out address
            :rtype: str | None
        """
        if host.find('address', {'addrtype': type}):
            return host.find('address', {'addrtype': type}).get('addr')
        return None

    def find_vendor(self, host: str) -> str | None:
        """
            Finds the vendor from host based on mac address and returns the string.

            :param host: The entire host tag string from the XML file
            :type: str

            :return: Parsed out vendor
            :rtype: str | None
        """
        if host.find('address', {'addrtype': 'mac'}):
            return host.find('address', {'addrtype': 'mac'}).get('vendor')
        return None

    def find_host_name(self, host: str) -> str | None:
        """
            Finds the hostname from host and returns the string.

            :param host: The entire host tag string from the XML file
            :type: str

            :return: Parsed out hostname
            :rtype: str | None
        """
        if host.find('hostname'):
            return host.find('hostname').get('name')
        return None
 
    def find_ports(self, host: str) -> list | None:
        """
            Find ports from host, form dictionaries based on important info, return a list of dictionaries.
        
            :param host: The entire host tag string from the XML file
            :type: str

            :return: List of dictionaries whose name are their port number
            :rtype: list | None
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

    def find_dhcp(self, host: str, type: str) -> str | None:
        """
            Finds dhcp server ip and router ip from host, then retuns the string.
        
            :param host: The entire host tag string from the XML file
            :param type: Dhcp or router
            :type: str

            :return: Parsed out address
            :rtype: str | None
        """ 
        if host.find('script'):
            if type == "dhcp":
                return host.find('script').find('elem', {'key': 'Server Identifier'}).string
            elif type == "router":
                return host.find('script').find('elem', {'key': 'Router'}).string
        return None
    
    def find_snmp(self, host: str, type: str) -> dict | None:
        """
            Finds information on snmp ports based on type, then returns a dictionary.

            :param host: The entire host tag string from the XML file
            :param type: snmp-sysdescr, snmp-info, snmp-interfaces, snmp-processes or snmp-win32-software
            :type: str

            :return: Dictionary of details respective to their type
            :rtype: dict | None
        """ 
        if host.find('script', {'id': type}):
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
            
            elif type == "snmp-interfaces":
                interface_list = list(host.find('script', {'id': 'snmp-interfaces'}).get('output').split("\n"))
                interface_list = [x for x in interface_list if x]   
                device_list = [(interface_list[0].lstrip())]  
                # The parameter "len(device_list)-1" indicates the position of the device in device_list is one position lower than the length of device_list.
                interface_dict = {device_list[len(device_list)-1]: {}}
                for interface in interface_list:
                    if device_list[len(device_list)-1] in interface:
                        pass
                    elif "IP address" in interface:
                        interface_dict[device_list[len(device_list)-1]].update({'ip': interface.split("IP address:")[1].split("Netmask")[0].strip()})
                        interface_dict[device_list[len(device_list)-1]].update({'mask': interface.split("Netmask:")[1].strip()})
                    elif "MAC address" in interface:
                        interface_dict[device_list[len(device_list)-1]].update({'mac': interface.split("MAC address:")[1].strip().split()[0]})
                        interface_dict[device_list[len(device_list)-1]].update({'vendor': interface.split("MAC address:")[1].strip().split()[1].strip("()")})
                    elif "Type" in interface:
                        interface_dict[device_list[len(device_list)-1]].update({'device_type': interface.split("Type:")[1].split("Speed:")[0].strip()})
                        interface_dict[device_list[len(device_list)-1]].update({'device_speed': interface.split("Type:")[1].split("Speed:")[1].lstrip()})
                    elif "Status" in interface:
                        interface_dict[device_list[len(device_list)-1]].update({'device_status': interface.split("Status:")[1].strip()})   
                    elif "Traffic stats" in interface:
                        interface_dict[device_list[len(device_list)-1]].update({'sent': interface.split("Traffic stats:")[1].split("sent")[0].strip()})
                        interface_dict[device_list[len(device_list)-1]].update({'received': interface.split("sent,")[1].split("received")[0].strip()})
                    else:
                        # If the data type is unrecognized then it might be a new device, add the new device name to device_list.
                        device_list.append(interface.lstrip())
                        interface_dict.update({device_list[len(device_list)-1]: {}})
                return interface_dict
        
            elif type == "snmp-processes":
                process_list = host.find('script', {'id': 'snmp-processes'}).find_all('table')
                process_dict = {}
                for process in process_list:
                    process_dict.update({process.get('key'): {}})
                    if process.find('elem', {'key': 'Name'}):
                        process_dict[process.get('key')].update({'name': process.find('elem', {'key': 'Name'}).string})
                    if process.find('elem', {'key': 'Path'}):
                        process_dict[process.get('key')].update({'path': process.find('elem', {'key': 'Path'}).string})
                    if process.find('elem', {'key': 'Params'}):
                        process_dict[process.get('key')].update({'parameters': process.find('elem', {'key': 'Params'}).string})
                return process_dict
            
            elif type == "snmp-win32-software":
                software_list = host.find('script', {'id': 'snmp-win32-software'}).find_all('table')
                software_dict = {}
                for software in software_list:
                    software_dict.update({software.find('elem', {'key': 'name'}).string.split(',')[1]: {}})
                    software_dict[software.find('elem', {'key': 'name'}).string.split(',')[1]].update({'vendor': software.find('elem', {'key': 'name'}).string.split(',')[0]})
                    software_dict[software.find('elem', {'key': 'name'}).string.split(',')[1]].update({'version': software.find('elem', {'key': 'name'}).string.split(',')[2]})
                    software_dict[software.find('elem', {'key': 'name'}).string.split(',')[1]].update({'install_date': software.find('elem', {'key': 'install_date'}).string})
                return software_dict
        return None
    
    def find_dns(self, data: str, type: str) -> dict | None:
        """
            Find dns caches and details of services from data then returns a dictionary.

            :param data: The entire data tag string from the XML file
            :param type: Service or cache
            :type: str

            :return: Dictionary of details respective to their type
            :rtype: dict | None
        """
        if type == "cache":
            if data.find('script', {'id': 'dns-cache-snoop'}):
                cache = data.find('script', {'id': 'dns-cache-snoop'}).get('output').split("\n")
                # Remove header.
                del cache[0]    
                return {self.find_address(data, "ipv4"): cache}

        elif type == "service":
            if data.find('prescript'):
                service_dict = {}
                extra_info = []
                service_list = data.find('script', {'id': 'broadcast-dns-service-discovery'}).get('output').strip().split("\n")
                # First entry of the output is mdns ip.
                del service_list[0] 
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
                        port_dict = {
                            'protocol': protocol,
                            'state': "open",
                            'service': service,
                            'extra_info': extra_info
                        }
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
    
    def find_wlan(self, network: str) -> tuple[bool, dict] | None:
        """
            Find basic info of all wireless networks near local machine and return a dictionary.

            :param network: The entire wireless-network tag string from the XML file
            :type: str

            :return: Tuple containing a boolean indicating if it's a hidden network and a dictionary of wireless network info
            :rtype: tuple[bool, dict] | None
        """
        if network.find('essid', {"cloaked": "false"}):
            essid = network.find('essid').string
        elif network.find('essid', {"cloaked": "true"}):
            essid = "hidden_network"
        bssid = network.find('BSSID').string
        manufacturer = network.find('manuf').string
        channel = network.find('channel').string
        frequency = network.find('freqmhz').string.split()[0]

        if network.find('encryption'):
            encrypt_list = network.find_all('encryption')
            encryption = []
            for data in encrypt_list:
                encryption.append(data.string)
        else:
            encryption = None

        if network.find('snr-info'):
            signal_dbm = network.find('snr-info').find('max_signal_dbm').string
        else:
            signal_dbm = None

        if float(network.find('SSID').find('max-rate').string) > 0:
            max_speed = int(float(network.find('SSID').find('max-rate').string))
            seen_speed = int(int(network.find('maxseenrate').string)/1000)
        else:
            max_speed = None

        if network.find('wireless-client', {'type': 'established'}):
            client_dict = {}
            for client in network.find_all('wireless-client', {'type': 'established'}):
                client_mac = client.find('client-mac').string
                client_manuf = client.find('client-manuf').string
                client_channel = client.find('channel').string
                client_speed = int(float(client.find('maxseenrate').string))
                client_signal_dbm = client.find('snr-info').find('max_signal_dbm').string
                established_client = {
                    'manufacturer': client_manuf,
                    'channel': client_channel,
                    'seen_speed': client_speed,
                    'signal_dbm': client_signal_dbm
                }
                client_dict.update({client_mac: established_client}) 
        else:
            client_dict = None

        if essid == "hidden_network":
            wlan_dict = {
                'manufacturer': manufacturer,
                'channel': channel,
                'frequency': frequency
            }
            if encryption:
                wlan_dict.update({'encryption': encryption})
            if signal_dbm:
                wlan_dict.update({'signal_dbm': signal_dbm})
            if max_speed:
                wlan_dict.update({'max_speed': max_speed})
                wlan_dict.update({'seen_speed': seen_speed})
            if client_dict:
                wlan_dict.update({'client': client_dict})

            return True, {bssid: wlan_dict}
        elif essid:
            wlan_dict = {
                'manufacturer': manufacturer,
                'channel': channel,
                'frequency': frequency
            }
            if encryption:
                wlan_dict.update({'encryption': encryption})
            if signal_dbm:
                wlan_dict.update({'signal_dbm': signal_dbm})
            if max_speed:
                wlan_dict.update({'max_speed': max_speed})
                wlan_dict.update({'seen_speed': seen_speed})
            if client_dict:
                wlan_dict.update({'client': client_dict})

            return False, {essid: {bssid: wlan_dict}}

            


class InvManager:
    """
        Receives data from FileChecker, sends it to Parser, receives parsed data back from Parser, then appends the parsed data to inventory.
    """
    def __init__(self):
        """
            Create net_inv which is the inventory for all processed data, create an instance for the Parser class
        """
        check = FileChecker("ip", "list")
        lan_inv = {}
        wlan_inv = {}
        for ip in check.ip_list:
            lan_inv.update({ip.strip(): {}})
            lan_inv[ip.strip()].update({'ports': {}})
        self.lan_inv = lan_inv
        self.wlan_inv = wlan_inv
        parse = Parser()
        self.parse = parse
    
    def basic_parser(self) -> None:
        """
            Adds hostname, mac address and vendor to inventory.
        """
        check = FileChecker("tcp", "log")
        for host in check.get_host():
            ip_address = self.parse.find_address(host, "ipv4")
            if ip_address in self.lan_inv:
                self.lan_inv[ip_address].update({'mac_address': self.parse.find_address(host, "mac")})
                self.lan_inv[ip_address].update({'vendor': self.parse.find_vendor(host)})
                self.lan_inv[ip_address].update({'hostname': self.parse.find_host_name(host)})
    
    def tcp_parser(self) -> None:
        """
            Adds detailed information for every tcp port in inventory.
        """
        check = FileChecker("tcp", "log")
        for host in check.get_host():
            ip_address = self.parse.find_address(host, "ipv4")
            if ip_address in self.lan_inv:
                if self.parse.find_ports(host):
                    for port_dict in self.parse.find_ports(host):
                        self.lan_inv[ip_address]['ports'].update(port_dict)
    
    def udp_parser(self) -> None:
        """
            Adds detailed information for every udp port in inventory.
        """
        check = FileChecker("udp", "log")
        for host in check.get_host():
            ip_address = self.parse.find_address(host, "ipv4")
            if ip_address in self.lan_inv:
                if self.parse.find_ports(host):
                    for port_dict in self.parse.find_ports(host):
                        self.lan_inv[ip_address]['ports'].update(port_dict)
    
    def port_parser(self) -> None:
        """
            Runs tcp and udp parser then checks for empty "ports" dictionary in inventory.
        """
        self.tcp_parser()
        self.udp_parser()
        for ip in self.lan_inv:
            if self.lan_inv[ip]['ports']:
                    pass
            else:
                self.lan_inv[ip].update({'ports': None})
   
    def dhcp_parser(self) -> None:
        """
            Adds dhcp server ip and router ip to inventory.
        """
        check = FileChecker("dhcp", "log")
        for host in check.get_host():
            self.lan_inv.update({'dhcp_server': self.parse.find_dhcp(host, "dhcp")})
            self.lan_inv.update({'router_ip': self.parse.find_dhcp(host, "router")})
     
    def snmp_parser(self) -> None:
        """
            Adds detailed snmp info to hosts that enable the snmp port.
        """ 
        check = FileChecker("snmp", "log")
        for host in check.get_host():
            ip_address = self.parse.find_address(host, "ipv4")
            if ip_address in self.lan_inv:
                self.lan_inv[ip_address].update({'snmp_info': {}})
                if self.parse.find_snmp(host, "snmp-sysdescr"):
                    self.lan_inv[ip_address]['snmp_info'].update(self.parse.find_snmp(host, "snmp-sysdescr"))
                if self.parse.find_snmp(host, "snmp-info"):
                    self.lan_inv[ip_address]['snmp_info'].update(self.parse.find_snmp(host, "snmp-info"))
                if self.parse.find_snmp(host, "snmp-interfaces"):
                    self.lan_inv[ip_address]['snmp_info'].update({'interfaces': self.parse.find_snmp(host, "snmp-interfaces")})
                if self.parse.find_snmp(host, "snmp-processes"):
                    self.lan_inv[ip_address]['snmp_info'].update({'processes': self.parse.find_snmp(host, "snmp-processes")})
                if self.parse.find_snmp(host, "snmp-win32-software"):
                    self.lan_inv[ip_address]['snmp_info'].update({'softwares': self.parse.find_snmp(host, "snmp-win32-software")})
                if self.lan_inv[ip_address]['snmp_info']:
                    pass
                else:
                    self.lan_inv[ip_address].update({'snmp_info': None})

    def dns_parser(self) -> None:
        """
            Use info from dns_log to update inventory infos that are empty, and add results of dns cache snoop to inventory.
        """
        check = FileChecker("dns", "log")
        self.lan_inv.update({'dns_cache': {}})
        for host in check.get_host():
            if self.parse.find_dns(host, "cache"):
                self.lan_inv['dns_cache'].update(self.parse.find_dns(host, "cache"))

        if self.parse.find_dns(check.data, "service"):
            dns_dict = self.parse.find_dns(check.data, "service")
            for ip in dns_dict:
                if ip in self.lan_inv:
                        for port in dns_dict[ip]:
                            if self.lan_inv[ip]['ports']:
                                if port in self.lan_inv[ip]['ports']:
                                    state = self.lan_inv[ip]['ports'][port]['state']
                                    if state == "closed" or state == "closed|filtered" or state == "open|filtered" or state == "filtered":
                                         self.lan_inv[ip]['ports'][port]['state'] = "open"
                                    if self.lan_inv[ip]['ports'][port]['service'] == None:
                                        self.lan_inv[ip]['ports'][port]['service'] = dns_dict[ip][port]["service"]
                                    if self.lan_inv[ip]['ports'][port]['extra_info'] == None:
                                        if dns_dict[ip][port]["extra_info"]:
                                            self.lan_inv[ip]['ports'][port]['extra_info'] = dns_dict[ip][port]["extra_info"]
                                else:
                                    self.lan_inv[ip]['ports'].update({port: dns_dict[ip][port]})
                            else:
                                self.lan_inv[ip]['ports']= {port: dns_dict[ip][port]}
    
    def wlan_parser(self) -> None:
        """
            Add wireless information near local machine to inventory.
        """
        check =FileChecker("wlan", "log")
        self.wlan_inv.update({'wireless_info': {}})
        for network in check.get_wlan():
            is_hidden, wlan_dict = self.parse.find_wlan(network)
            if is_hidden:
                if 'hidden_network' in self.wlan_inv['wireless_info']:
                    self.wlan_inv['wireless_info']['hidden_network'].update(wlan_dict)
                else:
                    self.wlan_inv['wireless_info'].update({'hidden_network': wlan_dict})
            elif next(iter(wlan_dict)) in self.wlan_inv['wireless_info']:
                self.wlan_inv['wireless_info'][next(iter(wlan_dict))].update(wlan_dict.get(next(iter(wlan_dict))))
            else:
                self.wlan_inv['wireless_info'].update(wlan_dict)

    def export(self, file_path: str, folder: str | None = "") -> None:
        """
            Runs the entire script then exports a JSON of the inventory.

            :param file_path: Destination for the JSON file
            :type: str

            :param folder: Folder name
            :type: str | None
        """
        self.basic_parser()
        self.port_parser()
        self.dhcp_parser()
        self.snmp_parser()
        self.dns_parser()
        self.wlan_parser()
        net_inv = {
            'LAN': self.lan_inv,
            'WLAN': self.wlan_inv
        }
        if folder:
            with open("../../"+folder+"/"+file_path+".json", "w") as file:
                json.dump(net_inv, file, indent=4)
        else:
            with open(file_path+".json", "w") as file:
                json.dump(net_inv, file, indent=4)
        print("Status: JSON file created successfully.")


def main():
    run = InvManager()
    now = datetime.now()
    # JSON file is named after time, so there will be no duplicates.
    time_of_creation = now.strftime("%Y_%b_%d_%H_%M")
    run.export(time_of_creation, "json")

if __name__ == "__main__":
    main()