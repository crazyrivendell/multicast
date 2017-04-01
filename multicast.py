# -*- coding: utf-8 -*-
#
# Send/receive UDP multicast packets.
# Requires that your OS kernel supports IP multicast.
#
# Usage:
#   python3.5 mcast -s (sender, IPv4)
#   python3.5 mcast -s -6 (sender, IPv6)
#   python3.5 mcast    (receivers, IPv4)
#   python3.5 mcast -6  (receivers, IPv6)

from __future__ import print_function
from __future__ import unicode_literals

import time
import struct
import socket
import sys
import select

DEVICE = 'Obsidian_1_0001'
MYPORT = 1900
PACK_SIZE = 1024
MYGROUP_4 = '239.192.1.1'
MYGROUP_6 = 'ff15:7079:7468:6f6e:6465:6d6f:6d63:6173'
MYTTL = 10  # Increase to reach other networks
TIME_PERIOD = 5

def main():
    group = MYGROUP_6 if "-6" in sys.argv[1:] else MYGROUP_4

    if "-s" in sys.argv[1:]:
        server(group)
    else:
        client(group)


def get_local_ip():
    try:
        csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        csock.connect(('8.8.8.8', 80))
        (address, port) = csock.getsockname()
        csock.close()
        return address
    except socket.error:
        return '127.0.0.1'

def server(group):
    addrinfo = socket.getaddrinfo(group, None)[0]
    s = socket.socket(addrinfo[0], socket.SOCK_DGRAM)


    # Set Time-to-live (optional)
    ttl_bin = struct.pack('@i', MYTTL)
    if addrinfo[0] == socket.AF_INET:  # IPv4
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
    else:
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)

    # set block
    # s.setblocking(1)
    i = 0
    _time = time.time()
    while True:
        # Send Search Message
        if time.time() - _time >= TIME_PERIOD:
            _time = time.time()
            _data = 'time is ' + time.asctime(time.localtime(time.time()))
            s.sendto(('Searching----' + _data).encode(), (addrinfo[4][0], MYPORT))

        # Receive Response Message
        try:
            _in, _out, _err = select.select([s, ], [], [], TIME_PERIOD)
            if len(_in) > 0:
                data, client = s.recvfrom(PACK_SIZE)
                print("Server receive data:\n", data, "\nfrom Client: ", client)
                i += 1
        except Exception as e:
            print('Error: ', str(e))
            pass
        print("cycle")


def client(group):
    # Look up multicast group address in name server and find out IP version
    addrinfo = socket.getaddrinfo(group, None)[0]

    # Create a socket
    s = socket.socket(addrinfo[0], socket.SOCK_DGRAM)

    # Allow multiple copies of this program on one machine
    # (not strictly needed)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind it to the port
    s.bind(('', MYPORT))
    # set block
    # s.setblocking(1)
    group_bin = socket.inet_pton(addrinfo[0], addrinfo[4][0])
    # Join group
    if addrinfo[0] == socket.AF_INET:  # IPv4
        mreq = group_bin + struct.pack('=I', socket.INADDR_ANY)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    else:
        mreq = group_bin + struct.pack('@I', 0)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

    # Loop, printing any data we receive
    i = 0
    while True:
        try:
            _in, _out, _err = select.select([s, ], [s,], [], None)
            if len(_in) > 0:
                # Receive Search Message
                data, client = s.recvfrom(PACK_SIZE)
                print("Client receive data:\n", data, "\nfrom Server: ", client)

                # Send Response Message
                _data = 'time is ' + time.asctime(time.localtime(time.time()))
                s.sendto(('Notifying----' + _data).encode(), client)
        except Exception as e:
            print('Error: ', str(e))
            pass


if __name__ == '__main__':
    main()

