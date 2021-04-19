import socket
from protocoln import RelProtocol
import sys
import time
import base64

server_addr = ('localhost', 6000)
# client_addr = ('localhost', 5000)
piece_size = 1024*1024*50
wind_size = 8

protocol = RelProtocol()

def sendFile(sock,filename,address):
    # f = open(filename,'rb')
    # file_data = base64.b64encode(f.read())
    # #print(len(file_data))
    # # file_data = str(file_data)
    # protocol.SRQsend(file_data,sock,address)

    with open(filename, 'rb') as f:
        while True:

            file_data = f.read(piece_size)
            if not file_data:
                break

            file_data = base64.b64encode(file_data)
            protocol.SRQsend(file_data,sock,address)
    


server_sock = protocol.makeSocket()
server_sock.bind(server_addr)


while True:
    filename, client_addr = protocol.threeWayConnect_sender(server_sock,wind_size)
    if filename!=0:
        break
    print("Reconnecting")
print(client_addr)

# while True:
# filename, client_addr = server_sock.recvfrom(1024) #address : from client
# ret_dict = protocol.recvPacket(server_sock,None)
# filename = filename.decode()
# filename = ret_dict['message']
#filename = 'plan.txt'
print(f"Received filename: {filename}")

sendFile(server_sock,filename,client_addr)

protocol.closeSocket(server_sock)