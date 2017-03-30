# multicast
multicast client server base on udp;  use C or Python

IP multicasting is supported only on AF_INET6 and AF_INET sockets of type SOCK_DGRAM and SOCK_RAW. IP multicasting is only supported on subnetworks for which the interface driver supports multicasting.

## Multicast Address
As you probably know, the range of IP addresses is divided into "classes" based on the high order bits of a 32 bits IP address:<br />  

    Bit --> 0                           31            Address Range:  <br />  
           +-+----------------------------+ <br />  
           |0|       Class A Address      |       0.0.0.0 - 127.255.255.255<br />  
           +-+----------------------------+<br />  
           +-+-+--------------------------+<br />  
           |1 0|     Class B Address      |     128.0.0.0 - 191.255.255.255<br />  
           +-+-+--------------------------+<br />  
           +-+-+-+------------------------+<br />  
           |1 1 0|   Class C Address      |     192.0.0.0 - 223.255.255.255<br />  
           +-+-+-+------------------------+<br />  
           +-+-+-+-+----------------------+<br />  
           |1 1 1 0|  MULTICAST Address   |     224.0.0.0 - 239.255.255.255<br />  
           +-+-+-+-+----------------------+<br />  
           +-+-+-+-+-+--------------------+<br />  
           |1 1 1 1 0|     Reserved       |     240.0.0.0 - 247.255.255.255<br />  
           +-+-+-+-+-+--------------------+<br />  

The one which concerns us is the "Class D Address". Every IP datagram whose destination address starts with "1110" is an IP Multicast datagram.<br />  

The remaining 28 bits identify the multicast "group" the datagram is sent to. Following with the previous analogy, you have to tune your radio to hear a program that is transmitted at some specific frequency, in the same way you have to "tune" your kernel to receive packets sent to an specific multicast group. When you do that, it's said that the host has joined that group in the interface you specified. More on this later.<br />  

There are some special multicast groups, say "well known multicast groups", you should not use in your particular applications due the special purpose they are destined to:<br />  

- 224.0.0.1 is the all-hosts group. If you ping that group, all multicast capable hosts on the network should answer, as every multicast capable host must join that group at start-up on all it's multicast capable interfaces.
- 224.0.0.2 is the all-routers group. All multicast routers must join that group on all it's multicast capable interfaces.
- 224.0.0.4 is the all DVMRP routers, 224.0.0.5 the all OSPF routers, 224.0.013 the all PIM routers, etc.

All this special multicast groups are regularly published in the "Assigned Numbers" RFC.<br />  

In any case, range 224.0.0.0 through 224.0.0.255 is reserved for local purposes (as administrative and maintenance tasks) and datagrams destined to them are never forwarded by multicast routers. Similarly, the range 239.0.0.0 to 239.255.255.255 has been reserved for "administrative scoping" (see section 2.3.1 for information on administrative scoping).<br />  

# Multicast Address
The following are the setsockopt()/getsockopt() function prototypes:<br />  

    int getsockopt(int s, int level, int optname, void* optval, int* optlen);
    int setsockopt(int s, int level, int optname, const void* optval, int optlen);
    
The first parameter, s, is the socket the system call applies to. For multicasting, it must be a socket of the family AF_INET and its type may be either SOCK_DGRAM or SOCK_RAW. The most common use is with SOCK_DGRAM sockets, but if you plan to write a routing daemon or modify some existing one, you will probably need to use SOCK_RAW ones.<br />  

The second one, level, identifies the layer that is to handle the option, message or query, whatever you want to call it. So, SOL_SOCKET is for the socket layer, IPPROTO_IP for the IP layer, etc... For multicast programming, level will always be IPPROTO_IP.<br />  

optname identifies the option we are setting/getting. Its value (either supplied by the program or returned by the kernel) is optval. The optnames involved in multicast programming are the following:<br />  

                            setsockopt()            getsockopt()
    IP_MULTICAST_LOOP           yes                     yes
    IP_MULTICAST_TTL            yes                     yes
    IP_MULTICAST_IF             yes                     yes
    IP_ADD_MEMBERSHIP           yes                      no
    IP_DROP_MEMBERSHIP          yes                      no

optlen carries the size of the data structure optval points to. Note that in getsockopt() it is a value-result rather than a value: the kernel writes the value of optname in the buffer pointed by optval and informs us of that value's size via optlen.<br />  
Both setsockopt() and getsockopt() return 0 on success and -1 on error.<br />  


## Sending IPv4 Multicast Datagrams
To send a multicast datagram, specify an IP multicast address in the range 224.0.0.0 to 239.255.255.255 as the destination address in a sendto call.<br />  
By default, IP multicast datagrams are sent with a time-to-live (TTL) of 1. This value prevents the datagrams from being forwarded beyond a single subnetwork. The socket option IP_MULTICAST_TTL allows the TTL for subsequent multicast datagrams to be set to any value from 0 to 255. This ability is used to control the scope of the multicasts.<br />  

    u_char ttl;
    setsockopt(sock, IPPROTO_IP, IP_MULTICAST_TTL, &ttl,sizeof(ttl))

Multicast datagrams with a TTL of 0 are not transmitted on any subnet, but can be delivered locally if the sending host belongs to the destination group and if multicast loopback has not been disabled on the sending socket. Multicast datagrams with a TTL greater than one can be delivered to more than one subnet if one or more multicast routers are attached to the first-hop subnet. To provide meaningful scope control, the multicast routers support the notion of TTL thresholds. These thresholds prevent datagrams with less than a certain TTL from traversing certain subnets. The thresholds enforce the conventions for multicast datagrams with initial TTL values as follows:<br />  

    0     Are restricted to the same host
    1     Are restricted to the same subnet
    32    Are restricted to the same site
    64    Are restricted to the same region
    128   Are restricted to the same continent
    255   Are unrestricted in scope

Sites and regions are not strictly defined and sites can be subdivided into smaller administrative units as a local matter.<br />  
An application can choose an initial TTL other than the ones previously listed. For example, an application might perform an expanding-ring search for a network resource by sending a multicast query, first with a TTL of 0 and then with larger and larger TTLs until a reply is received.<br />  

The multicast router does not forward any multicast datagram with a destination address between 224.0.0.0 and 224.0.0.255 inclusive, regardless of its TTL. This range of addresses is reserved for the use of routing protocols and other low-level topology discovery or maintenance protocols, such as gateway discovery and group membership reporting.<br />  

Each multicast transmission is sent from a single network interface, even if the host has more than one multicast-capable interface. If the host is also a multicast router and the TTL is greater than 1, a multicast can be forwarded to interfaces other than the originating interface. A socket option is available to override the default for subsequent transmissions from a given socket:<br />  

    struct in_addr addr;
    setsockopt(sock, IPPROTO_IP, IP_MULTICAST_IF, &addr, sizeof(addr))

where addr is the local IP address of the desired outgoing interface. Revert to the default interface by specifying the address INADDR_ANY. The local IP address of an interface is obtained with the SIOCGIFCONFioctl. To determine if an interface supports multicasting, fetch the interface flags with the SIOCGIFFLAGS ioctl and test if the IFF_MULTICAST flag is set. This option is intended primarily for multicast routers and other system services specifically concerned with Internet topology.<br />  
If a multicast datagram is sent to a group to which the sending host itself belongs, a copy of the datagram is, by default, looped back by the IP layer for local delivery. Another socket option gives the sender explicit control over whether subsequent datagrams are looped back:<br />  

    u_char loop;
    setsockopt(sock, IPPROTO_IP, IP_MULTICAST_LOOP, &loop, sizeof(loop))

where loop is 0 to disable loopback and 1 to enable loopback. This option provides a performance benefit for applications that have only one instance on a single host by eliminating the overhead of receiving their own transmissions. Applications that can have more than one instance on a single host, or for which the sender does not belong to the destination group, should not use this option.<br />  
If the sending host belongs to the destination group on another interface, a multicast datagram sent with an initial TTL greater than 1 can be delivered to the sending host on the other interface. The loopback control option has no effect on such delivery.<br />  
Receiving IPv4 Multicast DatagramsBefore a host can receive IP multicast datagrams, the host must become a member of one or more IP multicast groups. A process can ask the host to join a multicast group by using the following socket option:<br />  

    struct ip_mreq mreq;
    setsockopt(sock, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq))

where mreq is the structure:<br /> 

    struct ip_mreq {
        struct in_addr imr_multiaddr;   /* multicast group to join */
        struct in_addr imr_interface;   /* interface to join on */
    }

Each membership is associated with a single interface. You can join the same group on more than one interface. Specify the imr_interface address as INADDR_ANY to choose the default multicast interface. You can also specify one of the host's local addresses to choose a particular multicast-capable interface.<br />  
To drop a membership, use:<br />  

    struct ip_mreq mreq;
    setsockopt(sock, IPPROTO_IP, IP_DROP_MEMBERSHIP, &mreq, sizeof(mreq))

where mreq contains the same values used to add the membership. Closing a socket or killing the process that holds the socket drops the memberships associated with that socket. More than one socket can claim a membership in a particular group, and the host remains a member of that group until the last claim is dropped.<br />  

If any socket claims membership in the destination group of the datagram, the kernel IP layer accepts incoming multicast packets. A given socket's receipt of a multicast datagram depends on the socket's associated destination port and memberships, or the protocol type for raw sockets. To receive multicast datagrams sent to a particular port, bind to the local port, leaving the local address unspecified, such as INADDR_ANY.<br />  

More than one process can bind to the same SOCK_DGRAM UDP port if the bind(3SOCKET) is preceded by:<br />  

    int one = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one))

In this case, every incoming multicast or broadcast UDP datagram destined for the shared port is delivered to all sockets bound to the port. For backwards compatibility reasons, this delivery does not apply to incoming unicast datagrams. Unicast datagrams are never delivered to more than one socket, regardless of how many sockets are bound to the datagram's destination port. SOCK_RAW sockets do not require the SO_REUSEADDR option to share a single IP protocol type.<br />  

The definitions required for the new, multicast-related socket options are found in <netinet/in.h>. All IP addresses are passed in network byte-order.<br />  

##  Sending IPv6 Multicast Datagrams

To send an IPv6 multicast datagram, specify an IP multicast address in the range ff00::0/8 as the destination address in a sendto call.
By default, IP multicast datagrams are sent with a hop limit of one, which prevents the datagrams from being forwarded beyond a single subnetwork. The socket option IPV6_MULTICAST_HOPS allows the hop limit for subsequent multicast datagrams to be set to any value from 0 to 255. This ability is used to control the scope of the multicasts:<br />  

    uint_l;
    setsockopt(sock, IPPROTO_IPV6, IPV6_MULTICAST_HOPS, &hops,sizeof(hops))

You cannot transmit multicast datagrams with a hop limit of zero on any subnet, but you can deliver the datagrams locally if:<br />  
	* The sending host belongs to the destination group
	* Multicast loopback on the sending socket is enabled

You can deliver multicast datagrams with a hop limit that is greater than one to more than one subnet if the first-hop subnet attaches to one or more multicast routers. The IPv6 multicast addresses, unlike their IPv4 counterparts, contain explicit scope information that is encoded in the first part of the address. The defined scopes are, where X is unspecified:<br />  

    ffX1::0/16Node-local scope, restricted to the same node
    ffX2::0/16Link-local scope
    ffX5::0/16Site-local scope
    ffX8::0/16Organization-local scope
    ffXe::0/16Global scope

An application can, separately from the scope of the multicast address, use different hop limit values. For example, an application might perform an expanding-ring search for a network resource by sending a multicast query, first with a hop limit of 0, and then with larger and larger hop limits, until a reply is received.<br />  

Each multicast transmission is sent from a single network interface, even if the host has more than one multicast-capable interface. If the host is also a multicast router, and the hop limit is greater than 1, a multicast can be forwarded to interfaces other than the originating interface. A socket option is available to override the default for subsequent transmissions from a given socket:<br />  

    uint_t ifindex;
    ifindex = if_nametoindex ("hme3");
    setsockopt(sock, IPPROTO_IPV6, IPV6_MULTICAST_IF, &ifindex, sizeof(ifindex))

where ifindex is the interface index for the desired outgoing interface. Revert to the default interface by specifying the value 0.
If a multicast datagram is sent to a group to which the sending host itself belongs, a copy of the datagram is, by default, looped back by the IP layer for local delivery. Another socket option gives the sender explicit control over whether to loop back subsequent datagrams:<br />  

    uint_t loop;
    setsockopt(sock, IPPROTO_IPV6, IPV6_MULTICAST_LOOP, &loop, sizeof(loop))

where loop is zero to disable loopback and one to enable loopback. This option provides a performance benefit for applications that have only one instance on a single host (such as a router or a mail demon), by eliminating the overhead of receiving their own transmissions. Applications that can have more than one instance on a single host (such as a conferencing program) or for which the sender does not belong to the destination group (such as a time querying program) should not use this option.<br />  
If the sending host belongs to the destination group on another interface, a multicast datagram sent with an initial hop limit greater than 1 can be delivered to the sending host on the other interface. The loopback control option has no effect on such delivery.<br />  
Receiving IPv6 Multicast DatagramsBefore a host can receive IP multicast datagrams, the host must become a member of one, or more IP multicast groups. A process can ask the host to join a multicast group by using the following socket option:<br />  

    struct ipv6_mreq mreq;
    setsockopt(sock, IPPROTO_IPV6, IPV6_JOIN_GROUP, &mreq, sizeof(mreq))

where mreq is the structure:<br />  

    struct ipv6_mreq {
        struct in6_addr    ipv6mr_multiaddr;    /* IPv6 multicast addr */
        unsigned int       ipv6mr_interface;    /* interface index */
    }

Each membership is associated with a single interface. You can join the same group on more than one interface. Specify ipv6_interface to be 0 to choose the default multicast interface. Specify an interface index for one of the host's interfaces to choose that multicast-capable interface.<br />  

To leave a group, use:<br />

    struct ipv6_mreq mreq;
    setsockopt(sock, IPPROTO_IPV6, IP_LEAVE_GROUP, &mreq, sizeof(mreq))

where mreq contains the same values used to add the membership. The socket drops associated memberships when the socket is closed, or when the process that holds the socket is killed. More than one socket can claim a membership in a particular group. The host remains a member of that group until the last claim is dropped.<br />  

The kernel IP layer accepts incoming multicast packets if any socket has claimed a membership in the destination group of the datagram. Delivery of a multicast datagram to a particular socket is determined by the destination port and the memberships associated with the socket, or by the protocol type for raw sockets. To receive multicast datagrams sent to a particular port, bind to the local port, leaving the local address unspecified, such as INADDR_ANY.<br />  

More than one process can bind to the same SOCK_DGRAM UDP port if the bind is preceded by:<br />  

    int one = 1;
    setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one))

In this case, all sockets that are bound to the port receive every incoming multicast UDP datagram destined to the shared port. For backward compatibility reasons, this delivery does not apply to incoming unicast datagrams. Unicast datagrams are never delivered to more than one socket, regardless of how many sockets are bound to the datagram's destination port. SOCK_RAW sockets do not require the SO_REUSEADDR option to share a single IP protocol type.<br />  

The definitions required for the new, multicast-related socket options are found in <netinet/in.h>. All IP addresses are passed in network byte-order.<br />  

[refer](http://www.tldp.org/HOWTO/Multicast-HOWTO.html#toc7)<br />  

