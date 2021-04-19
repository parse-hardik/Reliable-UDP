# Reliable-UDP
## Changes in Initial Design
    1. Message size to be sent in each NSUU packet has been increased to 1024 bytes from 64 bytes, resulting in the  Data packet to be of 1317 bytes in total.
    2. Timeout time for each Data Packet is decreased to 0.5 sec.
    3. Max number of retransmissions after which the client is assumed to be disconnected is increased to 100.
    
## Steps to run client and server
	1. python3 server.py -p 6000
	2. python3 client.py -p 6000 -w 10
By default both server and client run on localhost, -p to the server implies the port on which server will be binded. -p to the client will indicate the port to which client should connect.
-w on client implies the window size desired.
Default values for port and window size are 6000 and 8 respectively.
By default client is binded on to port 5000, however, this is not necessary.
