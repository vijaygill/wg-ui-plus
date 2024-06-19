import ipaddress
import os
import re
import traceback


def ensure_folder_exists_for_file(filepath):
    dir = os.path.dirname(filepath)
    if not os.path.exists(dir):
        os.makedirs(dir)
        # logger.warning(f"Directory was missing. Created: {dir}")


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
    res = (False, None, None)
    try:
        ip = ipaddress.ip_interface(str(addr))
        if isinstance(addr, (ipaddress.IPv4Interface)):
            ip = addr
        res = (
            int(ip.ip) == int(ip.network.network_address) and ip.network.prefixlen < 32
        )
        res = (res, ip.ip, ip.network)
    except:
        pass
    return res


def get_target_ip_address_parts(value):
    regex = r"""
    ( ( (?P<ip1>\d{1,3} \. \d{1,3} \. \d{1,3} \. \d{1,3}) / (?P<mask> .+)  ) )
    | ( ( (?P<ip2>\d{1,3} \. \d{1,3} \. \d{1,3} \. \d{1,3}) : (?P<port> .+)  ) )
    | ( (?P<ip>\d{1,3} \. \d{1,3} \. \d{1,3} \. \d{1,3}) )
    """
    res = (False, None, None, None, None, None)
    errors = []
    try:
        matches = re.finditer(regex, value, re.MULTILINE | re.IGNORECASE | re.VERBOSE)
        for matchNum, match in enumerate(matches, start=1):
            ip = (
                match["ip2"]
                if match["ip2"]
                else match["ip1"] if match["ip1"] else match["ip"]
            )
            mask = match["mask"]
            port = match["port"]
            (
                target_is_network_address,
                target_ip_address,
                target_network_address,
            ) = is_network_address(ip)
            if mask:
                try:
                    mask = int(match["mask"])
                    mask_ok = 0 <= mask < 32
                    if not mask_ok:
                        errors.append(f"Invalid mask {mask}")
                    else:
                        (
                            target_is_network_address,
                            target_ip_address,
                            target_network_address,
                        ) = is_network_address(f'{ip}/{mask}')
                        res = (
                            mask_ok,
                            target_is_network_address,
                            target_ip_address,
                            target_network_address,
                            None,
                            mask,
                        )
                except:
                    errors.append(f"Invalid mask {mask}")
            elif port:
                ports = []
                ports_ok = True
                for p in port.split(","):
                    try:
                        pp = int(p)
                        if pp < 0 or pp > 65535:
                            errors.append(f"Invalid port: {p}")
                            ports_ok = False
                        else:
                            ports.append(pp)
                    except:
                        errors.append(f"Invalid port: {p}")
                        ports_ok = False
                if ports_ok and ports:
                    ports = sorted(ports)
                    res = (
                        is_single_address(ip),
                        target_is_network_address,
                        target_ip_address,
                        target_network_address,
                        ports,
                        None,
                    )
            else:
                ip_ok = is_single_address(ip)
                if not ip_ok:
                    errors.append(f"{ip} invalid for a host.")
                else:
                    res = (
                        ip_ok,
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
    r1, r2, r3, r4, r5, r6 = res
    errors = ", ".join(errors)
    res = (r1, r2, r3, r4, r5, r6, errors)
    return res
