
##Overview
Now that you have built a simple learning Ethernet switch and feel more comfortable with the Switchyard framework, you will get to do even more cool stuff using it. In this assignment, you are going to complete a series of tasks to eventually create a fully functional IPv4 router. At a high level, your router will have the following capabilities:

##Responding to/Making ARP requests
Receiving packets and forwarding them to their destination by using a lookup table
Responding to/Generating ICMP messages
Details
In order to create this cool router with the aforementioned capabilities, you will implement 5 main functionalities:

Respond to ARP (Address Resolution Protocol) requests for addresses that are assigned to interfaces on the router
Make ARP requests for IP addresses that have no known Ethernet MAC address. A router will often have to send packets to other hosts, and needs Ethernet MAC addresses to do so
Receive and forward packets that arrive on links and are destined to other hosts. Part of the forwarding process is to perform address lookups ("longest prefix match" lookups) in the forwarding information base. You will eventually just use "static" routing in your router, rather than implement a dynamic routing protocol like RIP or OSPF
Respond to Internet Control Message Protocol(ICMP) messages like echo requests ("pings")
Generate ICMP error messages when necessary, such as when an IP packet's TTL (time to live) value has been decremented to zero
You can find more detailed information on these functionalities on the following web pages:
Item #1 (NOTE: You will also implement the functionality that is described in One more note on the same page)
Item #2 and Item #3
Item #4 and Item #5
Address Resolution Protocol (ARP) Review
ARP is a protocol used for resolving IP addresses to MAC addresses. The main issue is that although IP addresses are used to forward IP packets across networks, a link-level address of the host or router to which you want to send the packet is required in a particular physical network. Therefore, hosts in the network need to keep a mapping between IP and link-layer addresses. Hosts can use ARP to broadcast query messages for a particular IP address in their physical networks so that the appropriate host can reply this query with its link-layer address.
Internet Control Message Protocol (ICMP) Review
ICMP is one of the main protocols that allows routers to closely monitor the operation of the Internet. ICMP messages are used by network devices (e.g routers) for sending error messages to indicate various issues, such as unreachable destination host/network or expired TTL for a packet. ping is a very commonly used network administration utility that uses ICMP Echo Request/Reply packets to validate the reachability of a host and also collect information about the status of the network (e.g average RTT, % of packet loss, etc.).
Testing your code
Just like the previous assignment, you should test the correctness of your implementation by writing your own test cases. As your friendly TA, I should warn you that in this assignment you will be implementing more functionalities and your router will be handling more events concurrently compared to the previous assignment. Therefore, you should think about reasonable ways to test the correctness of your implementation. One thing you can do is create test separate test cases that only tests certain functionalities. This will allow you to see whether the individual parts of your router is working properly. Then, you can generate larger test cases to make sure that the separate modules work together properly without breaking each other. As always, do not forget to consider corner cases (read: try to break your implementation).

Once you test your implementation with test scenarios, you can also test your router in Mininet. You can find more information on how to run Mininet tests for the aforementioned functionalities on their corresponding web pages.

Need a reminder on how to create test scenarios?
Test Scenarios
The test scenarios are broken down into three stages: 
Stage 1 (1st main functionality above), 
Stage 2 (2nd and 3rd main functionality), and 
Stage 3 (4th and 5th main functionality).

Test case for stage 1 provided here.
Note: Your code shouldn't be passing all the tests in this test file once they have stage 2 and 3 implemented, but should when just stage 1 is implemented
Test case for stage 2 provided here.
Note: This test should work even when stage 3 is implemented
Test case for stage 3 provided here.
Handing it in
For submitting your work, you should put the following files into a .tar.gz file. Name the file 
{student_number_of_partner1}_{student_number_of_partner2}.tar.gz
and email it to smcclanahan@wisc.edu by 5pm on 11/16 with the subject line [CS640] Submission P2.

myrouter.py: Your router implementation
README.txt: This file will contain a line for each student in your team: [name_of_student][single whitespace][10-digit UWID]
IMPORTANT: The file names in your handin directory has to exactly match the file names above. Otherwise, you will lose points!

Grading
This assignment will be graded similarly to the first project. 
1) All required files submitted by the deadline - 10 points 
2) myrouter.py passes a visual inspection and appears to implement the required functionality - 15 points 
3) myrouter.py passes automated functional tests - 25 points for each of these functionalities:

Responding to/Making ARP requests
Receiving packets and forwarding them to their destination by using a lookup table
Responding to/Generating ICMP messages
Notes
Great news! You can keep using the same development environment that you used for doing your first assignment. In case people removed their development environments or have decided to switch to the VM image that I provided, here are the useful information:
You can find the VM image here. (user name: cs640user - password: cs640)
You can learn more about importing a VM image in VirtualBox here. CSL machines already have VirtualBox installed so you should be able to use the image there without any problems. You are also free to use your favorite virtuaization software for importing the image but you will most probably have to deal with the possible issues on your
If you are a free soul and want to setup Switchyard in a different environment you are welcome to do that as well. You can find some useful information here. I prepared a file with commands that I have used to setup the Switchyard environment on Ubuntu 14.04. This might or might not be useful for you depending on your environment.
Documentation for Switchyard is available at http://cs.colgate.edu/~jsommers/switchyard/2017.01/
Instructions for submitting the assignment will be announced later.
I will update the FAQ if multiple people run into the same problems, so it might be useful to regularly check the FAQ. Otherwise, you can always shoot me an e-mail.
FAQ
Q: What should the router do in the following scenario? Packet for a certain IP address arrives at the router and it sends an ARP request to find the MAC address. Before receiving the ARP reply, the router receives another packet (non-ARP) for the same IP address, does it send an ARP request again?

A: No, in this case you do not retransmit the ARP request for the second packet. More generally, your router might receive many packets for a certain IP address while there is an outstanding ARP request for that IP address. In this case, your router should not send out any new ARP requests or update the timestamp of the initial ARP request. However, your router should buffer the new data packets so that it can transmit them to the destination host once it receives the ARP reply. IMPORTANT: If your router buffers multiple packets for a destination host that has an outstanding ARP request, upon receiving the corresponding ARP reply these packets has to be forwarded to the destination host in the order they arrived to the router!

Q: When an ARP request arrives at the router for a destination IP address that is not assigned to one of the router's interfaces, does the router need to flood the ARP request? Or just drop it?

A: Your router should drop the packet in this case. Note: In stage 1, you should be checking to see if the destination IP address is an IP address assigned to one of the router's interfaces. However, for stage two and three, check to see if the destination IP address is an IP address in the ARP table

Q: When the router needs to make an ARP request for the next hop IP address (which is obtained after the longest prefix match lookup), should it flood the request on all ports?

A: The router does not flood the ARP request on all ports. The ARP query is merely broadcast on the port obtained from doing a longest prefix match lookup. The response ARP query *should* come back on the same port but it doesn't actually need to (and it doesn't matter for the purposes of forwarding the packet or sending out the ARP request).

Q: When sending ICMP echo replies or error messages, does the router need to do table lookup & send ARP requests if needed? Can the router send the ICMP messages back on the interface through which the IP packet was received?

A: The router will still need to do an ARP query as it normally does for forwarding an IP packet. It doesn't matter that an echo request arrives on, say port 0. The echo reply may end up going out on a different port depending on the forwarding table lookup. The entire lookup and ARP query process should be the same as forwarding an IP packet, and will always behave exactly this way.

Q: How many error messages will be generated if a packet has TTL expired and network unreachable errors at the same time?

A: Your router will only generate a network unreachable error in this case. Since the router decrements the TTL field after doing a lookup, if the lookup fails then your router will not reach at decrementing the TTL value.

Q: Following up from Q1: if there are multiple packets buffered for the same destination host or next hop and the router doesn't receive an ARP reply after sending 5 retransmissions of ARP requests what should the router do?

A: As it is explained in the part 3 of the project, your router will send an ICMP destination host unreachable message back to the host referred to by the source address in the IP packet. When there are multiple packets buffered for the same destination address, the router will send an ICMP error message to each source host of these packets (even if the same source host sent multiple packets).

Q: Part of the instructions say if the packet is for us (i.e. it's destination ipaddr is in net.interfaces) then drop it. But later on, the instructions say that if the packet is meant for one of our directly connected neighbors then we forward it. How is net.interfaces() different than the directly connected networks.

A: The net.interfaces() is the information for the interfaces on the router itself. For example, eth1 might have an ipaddr of 192.168.1.1. However, from these interfaces you can use the ipaddr and netmask to get the subnet that the interface is directly connected to. So if the netmask of 255.255.255.0 for the same eth1, then the subnet would be the mask applied to the ipaddr which is 192.168.1.0. So, if a packet came to the router destined for an ip address like 192.168.1.100, then you would find a match in the forwarding table and end up forwarding the packet out eth1. But if a packet came to the router destined for 192.168.1.1, then you would drop it, since that is the exact ip address of the interface.

Q: In the instruction of our project, we are told that â€˜the echo reply may end up going out on a different port depending on the forwarding table lookup.' What does this mean?

A: The source ip address of the ICMP response does not necessarily need to be the ip address of the interface that you are sending the reply packet out of. The ICMP reply should have an ip.src and ip.dst that are the the ip.dst and ip.src of the ICMP request respectively (that is just switch them around). However, the destination address is looked up in the forwarding table to determine what port to send the reply out of. So the src ip address and the port of the ICMP reply may not match up to the same interface.
