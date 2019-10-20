import netifaces


def is_interface_up(interface):
    addr = netifaces.ifaddresses(interface)
    return addr.get(netifaces.AF_INET, False)
