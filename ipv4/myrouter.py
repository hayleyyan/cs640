#!/usr/bin/env python3

'''
Basic IPv4 router (static routing) in Python.
'''

import sys
import os
import time
from switchyard.lib.userlib import *
from collections import deque

# Class to hold the information of arp requests
class ARP_Request:

    def __init__(self, targetprotoaddr, senderhwaddr, senderprotoaddr, port_name, pkt):
        self.num_tries = 0
        self.try_time = time.time()
        self.ipaddr = targetprotoaddr
        self.senderprotoaddr = senderprotoaddr
        self.senderhwaddr = senderhwaddr
        self.port_name = port_name
        self.pkt_queue = deque()
        self.pkt_queue.append(pkt) 

class Router(object):

    def create_forwarding_table(self):
        table = []

        # Get table values from net.interfaces()
        for intf in self.net.interfaces():
            # Find network prefix append info to table
            prefix = IPv4Address(int(intf.ipaddr) & int(intf.netmask))
            table.append([str(prefix), str(intf.netmask), None, intf.name])

        # Get table values from file
        try:
            f = open("forwarding_table.txt")
            for line in f:
                entry = line.split(" ")
                entry[3] = entry[3].strip('\n') 
                table.append(entry)
            f.close()
        except FileNotFoundError:
            log_debug("File not found")

        return table


    def __init__(self, net):
        self.net = net
        # other initialization stuff here
         
        # Queue to keep track of arp requests sent out
        self.arp_queue = deque()

        # Dictionary to store IP and Ether MAC address pairs
        self.arp_table = {}

        # Forwarding Table
        self.forwarding_table = self.create_forwarding_table()  

        # Dictionary of router interface names mapped to their IP addresses
        self.router_interfaces = {}
        for intf in net.interfaces():
            self.router_interfaces[intf.name] = intf.ipaddr
            
    # Function iterates through queue of outstanding ARP requests and resends if necessary
    # Will drop the packet if it's sent 5 times
    def handle_arp_requests(self):
        new_queue = deque()
        for request in self.arp_queue:
            if time.time() - request.try_time >= 1:
                if request.num_tries < 5:
                    new_req = create_ip_arp_request(request.senderhwaddr, request.senderprotoaddr, request.ipaddr)
                    self.net.send_packet(self.net.interface_by_name(request.port_name), new_req)
                    request.num_tries += 1
                    new_queue.append(request)

                # If we've already tried 5 times without an ARP response, the host is unreachable, send error to source
                else:
                    self.create_icmp_error_pkt(request.packet_queue.popleft(), request.port_name, ICMPType.DestinationUnreachable, ICMPTypeCodeMap[ICMPType.DestinationUnreachable].HostUnreachable)
            else:
                new_queue.append(request)
        
        # Update our queue to have only requests we've sent less than 5 times
        self.arp_queue = new_queue
        

    # iterate through forwarding table to find the entry matching an IP packet
    def forwarding_table_lookup(self, dest):        
        maxprefix = 0
        matched_entry = None                    
        for entry in self.forwarding_table:
            prefixnet = IPv4Network(entry[0] + '/' + entry[1])
            matches = dest in prefixnet
 
            # If it matches, it checks if it has a longer prefix than the previous match (if applicable)
            if matches:
                netaddr = IPv4Network(entry[0] + '/' + entry[1])
                if netaddr.prefixlen >= maxprefix:
                    maxprefix = netaddr.prefixlen
                    matched_entry = entry
        return matched_entry

    # Creates a custom object to store an outstanding ARP request and necessary info to forward packets
    def create_arp_request(self, matched_entry, senderprotoaddr, targetprotoaddr, pkt):
        interface = self.net.interface_by_name(matched_entry[3])

        request_pkt = create_ip_arp_request(interface.ethaddr, senderprotoaddr, targetprotoaddr) 
        new_request = ARP_Request(targetprotoaddr, interface.ethaddr, senderprotoaddr, interface.name, pkt) 
        self.arp_queue.append(new_request)
 
        #TODO: this returns a NoneType has no ttl attribute error for ICMP time exceeded packet...
        self.net.send_packet(interface, request_pkt)
        new_request.num_tries += 1

    # Function to create and send an ICMP error packet - arguments include type and code for which error
    def create_icmp_error_pkt(self, pkt, input_port, icmptype, code):
        if pkt.has_header(Ethernet):
            i = pkt.get_header_index(Ethernet)
            del pkt[i]
        icmp_header = ICMP()
        icmp_header.icmptype = icmptype
        icmp_header.icmpdata.data = pkt.to_bytes()[:28]
        icmp_header.icmpcode = code
        ip_header = IPv4()
        ip_header.ttl = 64
        ip_header.src = self.net.interface_by_name(input_port).ipaddr
        ip_header.dst = pkt.get_header(IPv4).src
        
        icmp_err_pkt = ip_header + icmp_header
        if ip_header.dst in self.arp_table.keys():
            #create ethernet header and send
            dest_eth = self.arp_table[str(ip_header.dst)]
            src_eth = self.net.interface_by_name(input_port).ethaddr
            e = Ethernet(src = src_eth, dst = dest_eth)
            icmp_err_pkt.prepend_header(e)
            self.net.send_packet(self.interface_by_ipaddr(ip_header.dst), icmp_err_pkt) 

        else:
            entry = self.forwarding_table_lookup(ip_header.dst)
            self.create_arp_request(entry, self.net.interface_by_name(entry[3]).ipaddr, ip_header.dst, icmp_err_pkt)



    def router_main(self):    
        '''
        Main method for router; we stay in a loop in this method, receiving
        packets until the end of time.
        '''
        while True:
            gotpkt = True
            try:
                timestamp,dev,pkt = self.net.recv_packet(timeout=1.0)
            except NoPackets:
                log_debug("No packets available in recv_packet")
                gotpkt = False
            except Shutdown:
                log_debug("Got shutdown signal")
                break

            if gotpkt:
                log_debug("Got a packet: {}".format(str(pkt)))


                # Deal with an ARP packet
                if(pkt.has_header(Arp)):
                    arp = pkt.get_header(Arp)
                    # Deal with an ARP request
                    if arp.operation == 1:

                        # Add request information to arp table
                        if(arp.senderprotoaddr not in self.arp_table.keys()):
                            self.arp_table[arp.senderprotoaddr] = arp.senderhwaddr
                 
                        # Create an ARP reply if the destination address is attached to our router
                        if(arp.targetprotoaddr in self.router_interfaces.values()):
                            reply = create_ip_arp_reply(self.net.interface_by_ipaddr(arp.targetprotoaddr).ethaddr, arp.senderhwaddr, arp.targetprotoaddr, arp.senderprotoaddr)
                            self.net.send_packet(self.net.interface_by_name(dev), reply)
                            continue

                    # Deal with an ARP reply
                    else:
                        # Update ARP table with new info
                        eth = arp.senderhwaddr
                        self.arp_table[str(arp.senderprotoaddr)] = str(eth)

                        # Send packets queued for this request and remove from queue 
                        resolved = None
                        for request in self.arp_queue:
                            if str(request.ipaddr) in self.arp_table.keys():
                                for queued_packet in request.pkt_queue:
                                    if queued_packet.has_header(Ethernet):
                                        i = queued_packet.get_header_index(Ethernet)
                                        del queued_packet[i]
                                    e = Ethernet()
                                    e.dst = self.arp_table[str(request.ipaddr)]
                                    e.src = self.net.interface_by_name(request.port_name).ethaddr
                                    queued_packet.prepend_header(e)  
                                    self.net.send_packet(self.net.interface_by_name(request.port_name), queued_packet)
                                resolved = request 
                        if resolved is not None:
                            self.arp_queue.remove(resolved)
       
                # Deal with IP packet
                if(pkt.has_header(IPv4)):
                    ipv4 = pkt.get_header(IPv4)
                    dest = ipv4.dst
                   
                    #decrement TTL
                    ipv4.ttl -= 1  
                    # Send icmp error to source if ttl is zero                   
                    if ipv4.ttl <= 0:
                        self.create_icmp_error_pkt(pkt, dev, ICMPType.TimeExceeded, ICMPTypeCodeMap[ICMPType.TimeExceeded].TTLExpired)
                        continue


                    # Checking if the pkt is an ICMP request for one of our interfaces
                    if dest in self.router_interfaces.values() and pkt.has_header(ICMP):
                        icmp = pkt.get_header(ICMP)
                        if icmp.icmptype == 8:
                            # Create ICMP echo reply header
                            echo_reply = ICMP()
                            echo_reply.icmptype = 0
                            echo_reply.icmpdata.sequence = icmp.icmpdata.sequence
                            echo_reply.icmpdata.identifier = icmp.icmpdata.identifier
                            echo_reply.icmpdata.data = icmp.icmpdata.data

                            # Create IP header
                            new_ip = IPv4()
                            new_ip.dst = ipv4.src
                            new_ip.src = self.net.interface_by_name(dev).ipaddr
                            new_ip.ttl = 64 
                            
                            # Create the packet and add headers
                            reply_pkt = Packet()
                            reply_pkt += new_ip
                            reply_pkt += echo_reply 
                            
                            source_entry = self.forwarding_table_lookup(ipv4.src)
                            request_ip = self.net.interface_by_name(source_entry[3]).ipaddr
                             
                            if str(source_entry[2]) in self.arp_table.keys():
                                dest_eth = self.arp_table[source_entry[2]] 
                                src_eth = self.net.interface_by_name(dev).ethaddr
                                e = Ethernet(src = src_eth, dst = dest_eth)
                                reply_pkt.prepend_header(e) 
                                self.net.send_packet(self.net.interface_by_name(source_entry[3]), reply_pkt)
                            else: 
                                in_queue = False
                                
                                for request in self.arp_queue:
                                    if (request.ipaddr == new_ip.dst):
                                        request.pkt_queue.append(reply_pkt)
                                        in_queue = True

                                if not in_queue:
                                    if source_entry[2] is not None:
                                        self.create_arp_request(source_entry, request_ip, source_entry[2], reply_pkt)
                                    else:
                                        self.create_arp_request(source_entry, request_ip, self.net.interface_by_name(dev).ipaddr, reply_pkt)                    
                    else:
                        if dest in self.router_interfaces.values():
                            self.create_icmp_error_pkt(pkt, dev, ICMPType.DestinationUnreachable, ICMPTypeCodeMap[ICMPType.DestinationUnreachable].PortUnreachable)
                            continue

                    # Find the next hop via forwarding table
                        matched_entry = self.forwarding_table_lookup(dest)


                    # Processes the packet if a match was found
                        if matched_entry is not None: 
                        # If destination mac is already known, send packet
                            if str(dest) in self.arp_table.keys():
                                dest_eth = self.arp_table[str(dest)]
                                src_eth = self.net.interface_by_name(dev).ethaddr
                                e = Ethernet(src = src_eth, dst = dest_eth)
                                pkt.prepend_header(e)
                                self.net.send_packet(self.interface_by_ipaddr(str(dest), pkt)) 

                        
                        # Check for outstanding arp request or create one
                            else:
                                in_queue = False
                                for request in self.arp_queue:
                                    if (request.ipaddr == dest):
                                        request.pkt_queue.append(pkt)
                                        in_queue = True
                           
                                if not in_queue:
                                    if matched_entry[2] is not None:
                                        self.create_arp_request(matched_entry, matched_entry[2], dest, pkt)
                                    else:    
                                        self.create_arp_request(matched_entry, self.net.interface_by_name(matched_entry[3]).ipaddr, dest, pkt)
  
                        # No match found in forwarding table, create error packet and send
                        else:
                            self.create_icmp_error_pkt(pkt, dev, ICMPType.DestinationUnreachable, ICMPTypeCodeMap[ICMPType.DestinationUnreachable].NetworkUnreachable)


            self.handle_arp_requests()

                


def main(net):
    '''
    Main entry point for router.  Just create Router
    object and get it going.
    '''
    r = Router(net)
    r.router_main()
    net.shutdown()
