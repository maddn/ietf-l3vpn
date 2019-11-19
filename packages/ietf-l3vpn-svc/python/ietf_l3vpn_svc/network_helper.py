# -*- mode: python; python-indent: 4 -*-
_IPV4_SIZE = 32
_IPV4_MAX = 2 ** _IPV4_SIZE - 1


def get_ip_address(addr):
    """Return the Ip part of a 'Ip/Net' string."""
    parts = addr.split('/')
    return parts[0]


def get_ip_prefix(addr):
    """Return the Net part of a 'Ip/Net' string."""
    parts = addr.split('/')
    return int(parts[1])


def get_net_mask(addr):
    """Get the NetMask from a 'Ip/Net' string."""
    return prefix_to_net_mask(get_ip_prefix(addr))

def get_wildcard_mask(addr):
    """Get the Wildcard Mask from a 'Ip/Net' string."""
    return prefix_to_wildcard_mask(get_ip_prefix(addr))


def get_next_ipv4_address(addr):
    """Get the next succeeding IP address...hm..."""
    i = _ipv4_str_to_int(get_ip_address(addr)) + 1

    if i > _IPV4_MAX:
        raise ValueError("next IPV4 address out of bound")
    else:
        if (i & 0xff) == 255:
            i += 2

    return _ipv4_int_to_str(i)


def prefix_to_net_mask(prefix):
    """Transform a prefix (as string) to a netmask (as a string)."""
    return _ipv4_int_to_str(_prefix_to_net_mask(prefix))

def prefix_to_wildcard_mask(prefix):
    """Transform a prefix (as string) to a netmask (as a string)."""
    return _ipv4_int_to_str(_prefix_to_wildcard_mask(prefix))


def _prefix_to_wildcard_mask(prefix):
    """Transform an IP integer prefix to a wildcard mask integer."""
    if (prefix >= 0) and (prefix <= _IPV4_SIZE):
        return 2 ** (_IPV4_SIZE - prefix) - 1
    else:
        raise ValueError('IPV4 prefix out of bound')

def _prefix_to_net_mask(prefix):
    """Transform an IP integer prefix to a netmask integer."""
    if (prefix >= 0) and (prefix <= _IPV4_SIZE):
        return _IPV4_MAX ^ (2 ** (_IPV4_SIZE - prefix) - 1)
    else:
        raise ValueError('IPV4 prefix out of bound')

def _ipv4_str_to_int(addr):
    """Transform an IPV4 address string to an integer."""
    parts = addr.split('.')
    if len(parts) == 4:
        return (int(parts[0]) << 24) | (int(parts[1]) << 16) | \
            (int(parts[2]) << 8) | int(parts[3])
    else:
        raise ValueError('wrong format of IPV4 string')

def _ipv4_int_to_str(value):
    """Transform an IP integer to a string"""
    if (value >= 0) and (value <= _IPV4_MAX):
        return '%d.%d.%d.%d' % (value >> 24, (value >> 16) & 0xff,
                                (value >> 8) & 0xff, value & 0xff)
    else:
        raise ValueError('IPV4 value out of bound')
