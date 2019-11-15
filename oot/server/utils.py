import netifaces


def is_interface_up(interface):
    try:
        addr = netifaces.ifaddresses(interface)
    except ValueError:
        return False
    return addr.get(netifaces.AF_INET, False)
