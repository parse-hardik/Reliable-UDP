# Reliable-UDP
## Changes in Initial Design
    1. Message size to be sent in each NSUU packet has been increased to 1024 bytes from 64 bytes, resulting in the  Data packet to be of 1317 bytes in total.
    2. Timeout time for each Data Packet is decreased to 0.5 sec.
    3. Max number of retransmissions after which the client is assumed to be disconnected is increased to 100.
