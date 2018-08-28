#!/usr/bin/env python3

from switchyard.lib.address import *
from switchyard.lib.packet import *
from switchyard.lib.userlib import *
from random import randint
import time
import re
    
def send_packet(blastee_ip, net, RHS, l):
    '''
    Creating the headers for the packet
    '''
    pkt = Ethernet() + IPv4() + UDP()
    pkt[0].src = "10:00:00:00:00:01"
    pkt[0].dst = "40:00:00:00:00:02"
    pkt[1].src = IPv4Address("192.168.100.1")
    pkt[1].dst = IPv4Address(blastee_ip)
    pkt[1].protocol = IPProtocol.UDP

    '''
    Do other things here and send packet
    '''
    seq_num = RHS.to_bytes(4, byteorder='big')
    pkt.add_header(seq_num)
    length = l.to_bytes(2, byteorder='big')
    pkt.add_header(length)
    payload = (1024).to_bytes(l, byteorder='big')
    pkt.add_header(payload)
    net.send_packet(net.interface_by_macaddr("10:00:00:00:00:01"), pkt)

def switchy_main(net):
    my_intf = net.interfaces()
    mymacs = [intf.ethaddr for intf in my_intf]
    myips = [intf.ipaddr for intf in my_intf]

    # Initiate parameter variables
    file = open("blaster_params.txt")
    line = file.read().rstrip()
    params = re.split(r'-.\s', line)
    blastee_ip = params[1].rsplit()[0]
    num = int(params[2].rsplit()[0])
    length = int(params[3].rsplit()[0])
    sender_window = int(params[4].rsplit()[0])
    timeout = int(params[5].rsplit()[0])
    timeout = timeout/1000
    recv_timeout = int(params[6].rsplit()[0])
    recv_timeout = recv_timeout/1000

    # List will keep track of which packets have been acknowledged
    # Sequence number is index for each packet skipping 0 
    packet_sequence = [0]*(num+1)
    LHS = 1
    LHS_timer = time.time()
    RHS = 1
    retry_RHS = 1
    resending = False

    #statistics
    start_time = 0
    end_time = 0
    reTX = 0
    course_timeouts = 0
    total_sent = 0
    first_tries = 0

    while True:
        gotpkt = True
        try:
            #Timeout value will be parameterized!
            t,dev,pkt = net.recv_packet(timeout=recv_timeout)
        except NoPackets:
            log_debug("No packets available in recv_packet")
            gotpkt = False
        except Shutdown:
            log_debug("Got shutdown signal")
            break

        if gotpkt:
            log_debug("I got a packet")
            ack_bytes = pkt[3].data[:4]
            ack_int = int.from_bytes(ack_bytes, byteorder='big')
            packet_sequence[ack_int] += 1
            end_time = time.time()
 
            while packet_sequence[LHS] != 0:
                if LHS == num or LHS == RHS:
                    break
                LHS += 1
                LHS_timer = time.time()
 
            if LHS == num and packet_sequence[LHS] != 0:
                break


        else:
            log_debug("Didn't receive anything")

            if resending:
               while packet_sequence[retry_RHS-1] != 0 and retry_RHS < RHS:
                   retry_RHS += 1 
                   
               if retry_RHS >= RHS:
                   resending = False
                   LHS_timer = time.time()

               else:
                   total_sent += 1
                   reTX += 1
                   send_packet(blastee_ip, net, retry_RHS, length)
                   retry_RHS += 1 

            elif time.time() - LHS_timer >= timeout:
              course_timeouts += 1
              resending = True  
              retry_RHS = LHS
              total_sent += 1
              reTX += 1
              send_packet(blastee_ip, net, retry_RHS, length)
              retry_RHS += 1   

            elif RHS - LHS + 1 <= sender_window and RHS <= num:
                if RHS == 1:
                    start_time = time.time()
                send_packet(blastee_ip, net, RHS, length)
                RHS += 1
                total_sent += 1
                first_tries += 1

            

    total_time = end_time - start_time
    print("Total TX time (in seconds): " + str(total_time))
    print("Number of reTX: " + str(reTX))
    print("Number of course TOs: " + str(course_timeouts))
    print("Throughput (Bps): " + str((total_sent*length)/total_time))
    print("Goodput (Bps): " + str((first_tries*length)/total_time)) 
    net.shutdown()
