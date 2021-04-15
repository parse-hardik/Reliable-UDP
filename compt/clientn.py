import socket
from protocoln import RelProtocol
import sys
import base64

server_addr = ('localhost', 6000)
client_addr = ('localhost', 5000)

def recvFile(newFile,sock):
    ret_file, timed_out = protocol.SRQrecv(sock,server_addr)

    while timed_out == True and len(ret_file[0]) == 0:
    	print("Reconnecting")
    	while protocol.threeWayConnect_receiver(client_sock,server_addr,8,filename) == 0:
    		print("Reconnecting")

    	ret_file, timed_out = protocol.SRQrecv(sock,server_addr)

    # ret_file = bytes(ret_file.encode())
    # final_str = ""
    # ind = 0
    # while len(ret_file[ind]) != 0:
    # 	#print(len(ret_file[ind]))
    # 	final_str += ret_file[ind]
    # 	ind += 1

    # f = open(newFile,"wb")
    # f.write(final_str)

    ind = 0
    with open(newFile,"wb") as f:
    	while len(ret_file[ind]) != 0:
    		f.write(base64.b64decode(ret_file[ind]))
    		ind+=1


protocol = RelProtocol()
client_sock = protocol.makeSocket()
client_sock.bind(client_addr)
filename = 'logo.gif'
#print("called threeway")
while protocol.threeWayConnect_receiver(client_sock,server_addr,8,filename) == 0:
    print("Reconnecting")


print("sent to server")

newFile = f"client_{filename}"
recvFile(newFile,client_sock)

protocol.closeSocket(client_sock)