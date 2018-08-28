'''
Ethernet learning switch in Python.

Note that this file currently has the code to implement a "hub"
in it, not a learning switch.  (I.e., it's currently a switch
that doesn't learn.)
'''
from switchyard.lib.userlib import *
from collections import deque

def main(net):
    my_interfaces = net.interfaces() 
    mymacs = [intf.ethaddr for intf in my_interfaces]

    #table deque object  whose entries are a list in the form of [src, port]
    table = deque() 

    while True:
        try:
            timestamp,input_port,packet = net.recv_packet()

            #Loop checks if source address is already in the table
            inTable = False
            for entry in table:
                if entry[0] == packet[0].src:
                    inTable = True
                    #update the entry with the new port if it's changed
                    if entry[1] != input_port:
                        entry[1] = input_port

            #Add an entry for this source/port combo
            if inTable == False:  
                #remove least recently used entry if table is full
                if len(table) >= 5:
                    table.popleft()
                table.append([packet[0].src, input_port]) 

        except NoPackets:
            continue

        except Shutdown:
            return

        log_debug ("In {} received packet {} on {}".format(net.name, packet, input_port))
        if packet[0].dst in mymacs:
            log_debug ("Packet intended for me")

        #loop checks for the destination address in the table
        packetSent = False
        for entry in table:
            if entry[0] == packet[0].dst:
                for intf in my_interfaces:
                    #send packet on appropriate port
                    if intf.name == entry[1]:
                        net.send_packet(intf.name, packet)
                #save the entry with port used
                mru = entry
                packetSent = True
      
        #update table queue to have most recently used entry added to the end of the list
        if packetSent == True:
            dst, port = mru
            table.remove(mru)
            table.append([dst, port])

        #Destination address was not in table, so flood all ports with the packet
        else:
            for intf in my_interfaces:
                if input_port != intf.name:
                    log_debug ("Flooding packet {} to {}".format(packet, intf.name))
                    net.send_packet(intf.name, packet)
    net.shutdown()
