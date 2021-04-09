import socket
from protocoln import RelProtocol
import sys

server_addr = ('localhost', 6000)

def recvFile(newFile,sock):
    ret_file = protocol.SRQrecv(sock,server_addr)
    # ret_file = bytes(ret_file.encode())
    final_str = ""
    ind = 0
    while len(ret_file[ind]) != 0:
        final_str += ret_file[ind]
        ind += 1

    f = open(newFile,"w")
    f.write(final_str)

protocol = RelProtocol()
client_sock = protocol.makeSocket()
filename = input('Enter file name: ')
#print("called threeway")
while protocol.threeWayConnect_receiver(client_sock,server_addr,8,filename) == 0:
    print("Reconnecting")

# protocol.threeWayConnect()

# protocol.sendDataPacket(0,0,0,0,filename,client_sock,server_addr)
# client_sock.sendto(bytes(filename.encode()),server_addr)
print("sent to server")

newFile = f"client_{filename}"
recvFile(newFile,client_sock)

protocol.closeSocket(client_sock)