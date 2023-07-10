# -*- coding: utf-8 -*-
# @Time： 2023/7/10 21:15 
# @FileName: IP.py
# @Software： PyCharm
# @GitHub: KimmyXYC
import ipaddress
import socket


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
        ip_address = socket.gethostbyname(domain)
        return ip_address
    except socket.gaierror:
        return None
