import os
import ipaddress
import re
import traceback

def ensure_folder_exists_for_file(filepath):
    dir = os.path.dirname(filepath)
    if not os.path.exists(dir):
        os.makedirs(dir)
        logger.warning(f"Directory was missing. Created: {dir}")


def is_single_address(value):
    res = False
    try:
        ip = ipaddress.ip_interface(str(value))
        if isinstance(value, (ipaddress.IPv4Interface)):
            ip = value
        res = ip.network.prefixlen == 32
    except:
        res = False
    return res


def is_network_address(addr):
    ip = ipaddress.ip_interface(str(addr))
    if isinstance(addr, (ipaddress.IPv4Interface)):
        ip = addr
    res = int(ip.ip) == int(ip.network.network_address) and ip.network.prefixlen < 32
    return (res, ip.ip, ip.network)


def ensure_folder_exists_for_file(filepath):
    dir = os.path.dirname(filepath)
    if not os.path.exists(dir):
        os.makedirs(dir)
        logger.warning(f"Directory was missing. Created: {dir}")

def get_target_ip_address_parts(value):
    regex = r"""
	( ( (?P<ip1>\d{1,3} \. \d{1,3} \. \d{1,3} \. \d{1,3}) / (?P<mask> .+)  ) )
	| ( ( (?P<ip2>\d{1,3} \. \d{1,3} \. \d{1,3} \. \d{1,3}) : (?P<port> .+)  ) )
	| ( (?P<ip>\d{1,3} \. \d{1,3} \. \d{1,3} \. \d{1,3}) )
	"""
    res = (False, None, None, None, None, None)
    try:
        matches = re.finditer(regex, value, re.MULTILINE | re.IGNORECASE | re.VERBOSE)
        for matchNum, match in enumerate(matches, start=1):
            ip = match["ip2"] if match["ip2"] else match["ip1"] if match["ip1"] else match["ip"]
            mask = match["mask"]
            port = match["port"]
            (
                target_is_network_address,
                target_ip_address,
                target_network_address,
            ) = is_network_address(ip)
            if mask:
                mask = int(match["mask"])
                res = (
                    True and mask < 32,
                    target_is_network_address,
                    target_ip_address,
                    target_network_address,
                    None,
                    mask,
                )
            elif port:
                port = int(port)
                res = (
                    is_single_address(ip) and port < 65535,
                    target_is_network_address,
                    target_ip_address,
                    target_network_address,
                    port,
                    None,
                )
            else:
                res = (
                    is_single_address(ip),
                    target_is_network_address,
                    target_ip_address,
                    target_network_address,
                    None,
                    None,
                )
            break
    except:
        print(traceback.format_exc())
        pass
    return res
