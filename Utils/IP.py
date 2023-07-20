# -*- coding: utf-8 -*-
# @Time: 2023/7/10 21:15 
# @FileName: IP.py
# @Software: PyCharm
# @GitHub: KimmyXYC
import ipaddress
import socket
import requests
from loguru import logger


def check_url(url):
    try:
        ip = ipaddress.ip_address(url)
        if ip.version == 4:
            return url, "v4"
        elif ip.version == 6:
            return url, "v6"
    except ValueError:
        return get_ip_address(url), None


def get_ip_address(domain):
    try:
        addr_info = socket.getaddrinfo(domain, None, socket.AF_UNSPEC)
        ip_addresses = []
        for info in addr_info:
            ip_address = info[4][0]
            ip_addresses.append(ip_address)
        return ip_addresses[0]
    except socket.gaierror as e:
        logger.error(f"Domain name resolution failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unknown error: {e}")
        return None


def ali_ipcity_ip(ip_addr, appcode, is_v6=False):
    if is_v6:
        url = "https://ipv6city.market.alicloudapi.com/ip/ipv6/query"
    else:
        url = "https://ipcity.market.alicloudapi.com/ip/city/query"
    headers = {"Authorization": "APPCODE {}".format(appcode)}
    params = {"ip": ip_addr}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["code"] == 200:
            return True, data["data"]["result"]
        else:
            return False, data["msg"]


def kimmy_ip(ip_addr):
    url = "https://api.kimmyxyc.top/ip"
    params = {"ip": ip_addr}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["code"] == 0:
            return True, data["data"]
        else:
            return False, data["data"]["error"]


def ipapi_ip(ip_addr):
    url = f"http://ip-api.com/json/{ip_addr}"
    params = {"fields": "status,message,country,regionName,city,lat,lon,isp,org,as,mobile,proxy,hosting,query"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["status"] == "success":
            return True, data
        else:
            return False, data


def icp_record_check(domain):
    url = f" https://api.emoao.com/api/icp"
    params = {"domain": domain}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["code"] == "200":
            return True, data
        else:
            return False, data["msg"]


def whois_check(domain):
    response = requests.get(f'https://namebeta.com/api/search/check?query={domain}')
    if response.status_code == 200:
        result = response.json()['whois']
        if "whois" not in result:
            return False, result
        result = result['whois']
        lines = result.splitlines()
        filtered_result = [line for line in lines if
                           'REDACTED FOR PRIVACY' not in line and 'Please query the' not in line]
        return True, "\n".join(filtered_result).split("For more information")[0]
    else:
        return False, None


def get_dns_info(domain, record_type):
    qtype = {
        "A": 1,
        "NS": 2,
        "CNAME": 5,
        "MX": 15,
        "TXT": 16,
        "AAAA": 28,
    }
    if record_type not in qtype.keys():
        return False, "record_type error"
    url = f"https://myssl.com/api/v1/tools/dns_query"
    params = {
        "qtype": qtype[record_type],
        "host": domain,
        "qmode": -1
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data["code"] == 0:
            return True, data["data"]
        else:
            return False, data["error"]
    else:
        return False, None
