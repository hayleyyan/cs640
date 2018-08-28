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
    
    #table deque object whose entries are a list in the form of [src, port, traffic_volume]
    table = deque() 

    while True:
        try:
            timestamp,input_port,packet = net.recv_packet()

            #Loop checks if source address is already in the table
            inTable = False
            for entry in table:
                if entry[0] == packet[0].src:
                    inTable = True
                    #Update the entry in table if port has changed for the source address
                    if entry[1] != input_port:
                        entry[1] = input_port

            #Add the entry to the table if necessary
            if inTable == False:  
                #Check if table is full and delete least used entry if so
                if len(table) >= 5:
                    minVol = table[0]
                    for entry in table:
                        if entry[2] < minVol[2]:
                            minVol = entry
                    table.remove(minVol)
                table.append([packet[0].src, input_port, 0])
 
        except NoPackets:
            continue

        except Shutdown:
            return

        log_debug ("In {} received packet {} on {}".format(net.name, packet, input_port))
        if packet[0].dst in mymacs:
            log_debug ("Packet intended for me")

        #Loop checks if destination address is in the table
        packetSent = False
        for entry in table:
            if entry[0] == packet[0].dst:
                for intf in my_interfaces:
                    #Send packet on appropriate port
                    if intf.name == entry[1]:
                        net.send_packet(intf.name, packet)
                used = entry
                packetSent = True
      
        #Increment the traffic volume of the entry used
        if packetSent == True:
            used[2] += 1

        #Flood all ports with the packet if the destination was not in the table
        else:
            for intf in my_interfaces:
                if input_port != intf.name:
                    log_debug ("Flooding packet {} to {}".format(packet, intf.name))
                    net.send_packet(intf.name, packet)
    net.shutdown()
