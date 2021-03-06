#!/usr/bin/env python
import sys 
import struct
import os
import threading

"""
from scapy.all import sniff, sendp, hexdump, get_if_list, get_if_hwaddr
from scapy.all import Packet, IPOption
from scapy.all import ShortField, IntField, LongField, BitField, FieldListField, FieldLenField
from scapy.all import IP, TCP, UDP, Raw, DNS
from scapy.all import rdpcap
"""
from scapy.all import *
from scapy.layers.inet import _IPOption_HDR

def get_if():
    ifs=get_if_list()
    iface=None
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break;
    if not iface:
        print "Cannot find eth0 interface"
        exit(1)
    return iface

class IPOption_MRI(IPOption):
    name = "MRI"
    option = 31
    fields_desc = [ _IPOption_HDR,
                    FieldLenField("length", None, fmt="B",
                                  length_of="swids",
                                  adjust=lambda pkt,l:l+4),
                    ShortField("count", 0),
                    FieldListField("swids",
                                   [],
                                   IntField("", 0),
                                   length_from=lambda pkt:pkt.count*4) ]

def handle_pkt(pkt, socket, r_pkt):
    if UDP in pkt and pkt[UDP].dport == 53:
        global r_num
        if r_num%10 == 1:
            print "Get  %4dst packet, id: %5d"%(r_num,pkt.getlayer(DNS).id)
        elif r_num%10 == 2:
            print "Get  %4dst packet, id: %5d"%(r_num,pkt.getlayer(DNS).id)
        elif r_num%10 == 3:
            print "Get  %4dst packet, id: %5d"%(r_num,pkt.getlayer(DNS).id)
        else:
            print "Get  %4dst packet, id: %5d"%(r_num,pkt.getlayer(DNS).id)
        r_num += 1
        # print pkt.show()
        sys.stdout.flush()
        pass_pkt(pkt, r_pkt[str(pkt[DNS].id)+str(pkt.qd)], socket)
        # for rp in r_pkt:
            # if pkt[DNS].id == rp[DNS].id and pkt.qd == rp.qd:
                # pass_pkt(pkt, rp)
        #         break


    #    hexdump(pkt)

def pass_pkt(q,r, socket):
    # p = Ether(src = q[Ether].dst, dst=q[Ether].src)
    p = Ether(src = get_if_hwaddr(iface), dst="FF:FF:FF:FF:FF:FF")
    # print "Ether_src: ", q[Ether].src
    p = p / IP(dst=q[IP].src) / UDP(dport=q[UDP].sport, sport=53) / r.getlayer(DNS)
    global s_num
    if s_num%10 == 1:
        print "Send %4dst packet, id: %5d"%(s_num,p.getlayer(DNS).id)
    elif s_num%10 == 2:
        print "Send %4dnd packet, id: %5d"%(s_num,p.getlayer(DNS).id)
    elif s_num%10 == 3:
        print "Send %4drd packet, id: %5d"%(s_num,p.getlayer(DNS).id)
    else:
        print "Send %4dth packet, id: %5d"%(s_num,p.getlayer(DNS).id)
    s_num += 1
    # print p.show()
    # global socket
    sendp(p, iface = iface, verbose=False, socket=socket)

def distribute_thread(pkt, socket, r_pkt):
    tmp_pkt = dict(r_pkt)
    t = threading.Thread(target=handle_pkt, args=(pkt,socket,tmp_pkt,))
    t.setDaemon(True)
    t.start()

def main():
    ifaces = filter(lambda i: 'eth' in i, os.listdir('/sys/class/net/'))
    global iface
    iface = ifaces[0]
    print("iface: ", iface)
    # global socket
    socket = conf.L2socket(iface=iface) 

    #if len(sys.argv) < 2:
    #    print("pass 1 argument: <file.pcap>")
    #    exit(1)

    # global pcaps # store the packets from .pcap
    # global r_pkt # store the packets is received
    
    #pcaps = rdpcap(sys.argv[1])
    pcaps = rdpcap("dns0313_2_onlyDNS.pcapng")
    r_pkt = {}

    for pkt in pcaps:
        if pkt.qr == 1: # the packet is response
            r_pkt[str(pkt[DNS].id)+str(pkt.qd)] = pkt


    print "sniffing on %s" % iface
    sys.stdout.flush()
    sniff(iface = iface,
          prn = lambda x: distribute_thread(x, socket, r_pkt))

if __name__ == '__main__':
    s_num = 0
    r_num = 0
    main()
