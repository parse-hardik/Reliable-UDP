import socket
from protocoln import RelProtocol
import sys
import time

server_addr = ('localhost', 6000)

protocol = RelProtocol()

def sendFile(sock,filename,address):
    f = open(filename,'r')
    file_data = f.read()
    # file_data = str(file_data)
    protocol.SRQsend(file_data,sock,address)
    


server_sock = protocol.makeSocket()
server_sock.bind(server_addr)


while True:
    client_addr, filename = protocol.threeWayConnect_sender(server_sock,8)
    if client_addr!=0:
        break
print(client_addr)

# while True:
# filename, client_addr = server_sock.recvfrom(1024) #address : from client
# ret_dict = protocol.recvPacket(server_sock,None)
# filename = filename.decode()
# filename = ret_dict['message']
print(f"Received filename: {filename}")

sendFile(server_sock,filename,client_addr)

protocol.closeSocket(server_sock)