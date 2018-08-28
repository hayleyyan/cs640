'''
Ethernet learning switch in Python.

Note that this file currently has the code to implement a "hub"
in it, not a learning switch.  (I.e., it's currently a switch
that doesn't learn.)
'''
from switchyard.lib.userlib import *
from collections import deque
import time 

def main(net):
    my_interfaces = net.interfaces() 
    mymacs = [intf.ethaddr for intf in my_interfaces]
   
    #forwarding table list whose entries are a list in 
    #the form of [src, port, time]
    table = [] 

    while True:
        try:
            timestamp,input_port,packet = net.recv_packet()
           
            #Loop checks if the source address is already in our table
            inTable = False 
            for entry in table:
                if entry[0] == packet[0].src:
                    inTable = True
                    #update port for the entry if it has changed
                    if entry[1] != input_port:
                        entry[1] = input_port
                    entry[2] = time.time()

            #Add an entry for this source address, port combo
            if inTable == False:  
                table.append([packet[0].src, input_port, time.time()])
 
        except NoPackets:

            #update the table only with entries used in the last 10 seconds
            table[:] = [entry for entry in table if (time.time()-entry[2] < 10)]

            continue

        except Shutdown:
            return

        log_debug ("In {} received packet {} on {}".format(net.name, packet, input_port))
        if packet[0].dst in mymacs:
            log_debug ("Packet intended for me")

        #loop checks if the destination address is in the forwarding table
        packetSent = False
        for entry in table:
            if entry[0] == packet[0].dst:
                for intf in my_interfaces:
                    #send the packet on the associated port
                    if intf.name == entry[1]:
                        net.send_packet(intf.name, packet)
                used = entry
                packetSent = True

        #if address was not found in the table, flood all ports with packet
        if packetSent == False:
            for intf in my_interfaces:
                if input_port != intf.name:
                    log_debug ("Flooding packet {} to {}".format(packet, intf.name))
                    net.send_packet(intf.name, packet)
    net.shutdown()
