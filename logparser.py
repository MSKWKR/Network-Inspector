#!usr/bin/env python

from bs4 import BeautifulSoup

data_dict = {}
ipv4_list = []
with open('./log/ping_log.xml', 'r') as f:
    log = f.read()

Bs_data = BeautifulSoup(log, "xml")


xml_ipv4 = Bs_data.find_all('address', {'addrtype':'ipv4'})
for ipv4 in xml_ipv4:
    ipv4_list.append(ipv4.get('addr'))
    data_dict[ipv4.get('addr')] = {}

xml_address = Bs_data.find_all('address')
for data in xml_address:
    if data.get('addr') in ipv4_list:
        inlist = True
        temp_ip = data.get('addr')
    else: 
        inlist = False
    if inlist == False:
        data_dict[temp_ip].update({"mac_address": data.get('addr')})
        data_dict[temp_ip].update({"vendor": data.get('vendor')})




    
