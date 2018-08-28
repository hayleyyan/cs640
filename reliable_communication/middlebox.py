#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.userlib import *
from threading import *
import random
import time

def get_drop_rate():
    try:
        file = open("middlebox_params.txt")
        line = file.read()
        rate_string = line[3:].rstrip()
        file.close()
        
    except FileNotFoundError:
        log_debug("File not found")

    return float(rate_string)

def switchy_main(net):

    my_intf = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_intf]
    myips = [intf.ipaddr for intf in my_intf]
    drop_rate = get_drop_rate()

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
            log_debug("I got a packet {}".format(pkt))

        if dev == "middlebox-eth0":
            log_debug("Received from blaster")
            '''
            Received data packet
            Should I drop it?
            If not, modify headers & send to blastee
            '''
            r = random.random()
            if r <= drop_rate:
                continue

            pkt[0].src = "40:00:00:00:00:02"
            pkt[0].dst = "20:00:00:00:00:01"

            net.send_packet("middlebox-eth1", pkt)
        elif dev == "middlebox-eth1":
            log_debug("Received from blastee")
            '''
            Received ACK
            Modify headers & send to blaster. Not dropping ACK packets!
            '''
            
            pkt[0].src = "40:00:00:00:00:01"
            pkt[0].dst = "10:00:00:00:00:01"
            
            net.send_packet("middlebox-eth0", pkt)

        else:
            log_debug("Oops :))")

    net.shutdown()
