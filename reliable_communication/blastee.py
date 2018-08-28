#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.userlib import *
from threading import *
import time
import re

def switchy_main(net):
    my_interfaces = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_interfaces]

    file = open("blastee_params.txt")
    line = file.read().rstrip()
    params = re.split(r'-.\s', line)
    blaster_ip = params[1].rsplit()[0]

    while True:
        gotpkt = True
        try:
            t,dev,pkt = net.recv_packet()
            log_debug("Device is {}".format(dev))
        except NoPackets:
            log_debug("No packets available in recv_packet")
            gotpkt = False
        except Shutdown:
            log_debug("Got shutdown signal")
            break

        if gotpkt:
            log_debug("I got a packet from {}".format(dev))
            log_debug("Pkt: {}".format(pkt))

            ack_pkt = Ethernet() + IPv4() + UDP()
            ack_pkt[0].src = pkt[0].dst
            ack_pkt[0].dst = pkt[0].src
            ack_pkt[1].src = pkt[1].dst
            ack_pkt[1].dst = IPv4Address(blaster_ip)
            ack_pkt[1].protocol = IPProtocol.UDP

            seq_num = pkt[3].data[:4]
            ack_pkt.add_header(seq_num)
            payload = (0).to_bytes(8, byteorder='big')
            ack_pkt.add_header(payload)
            net.send_packet(net.interface_by_macaddr("20:00:00:00:00:01"), ack_pkt)

    net.shutdown()
