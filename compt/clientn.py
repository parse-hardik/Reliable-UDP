import socket
from protocoln import RelProtocol
import sys
import base64
import threading
import os

server_addr = ('localhost', 6000)
#client_addr = ('localhost', 5000)
piece_size = 1024*1024
bytes_recv = 0
wind_size = 100

def end_func():
    print(bytes_recv)

def recvFile(newFile,sock):
    # ret_file, timed_out = protocol.SRQrecv(sock,server_addr)

    # while timed_out == True and len(ret_file[0]) == 0:
    # 	print("Reconnecting")
    # 	while protocol.threeWayConnect_receiver(client_sock,server_addr,8,filename) == 0:
    # 		print("Reconnecting")

    # 	ret_file, timed_out = protocol.SRQrecv(sock,server_addr)

    # ind = 0
    # with open(newFile,"wb") as f:
    # 	while len(ret_file[ind]) != 0:
    # 		f.write(base64.b64decode(ret_file[ind]))
    # 		ind+=1
    global bytes_recv
    done_handshake = False
    timer_started = False
    f = open(newFile,"wb")
    
    # t=threading.Timer(60, end_func)
    # t.start()
    t = threading.Timer(60, end_func)
    while True:
        ret_file, timed_out = protocol.SRQrecv(sock,server_addr)

        while timed_out == True and len(ret_file[0]) == 0 and done_handshake == False:
            print("Reconnecting")
            while protocol.threeWayConnect_receiver(client_sock,server_addr,wind_size,filename) == 0:
                print("Reconnecting")

            ret_file, timed_out = protocol.SRQrecv(sock,server_addr)
            if timed_out == False or len(ret_file[0]) != 0 or done_handshake == True:
                done_handshake = True

                break

        if len(ret_file[0]) == 0:
            continue

        if timer_started == False:
            #t.start()

            timer_started = True

        ind = 0
        curr_size = 0
        #with open(newFile,"wb") as f:
        while len(ret_file[ind]) != 0:
            ret_file[ind] = base64.b64decode(ret_file[ind])
            curr_size += len(ret_file[ind])
            f.write(ret_file[ind])
            ind+=1

        bytes_recv += curr_size
        if curr_size < piece_size:
            print("Done Transfer")
            print(curr_size)
            break

    #t.join()
    f.close()


protocol = RelProtocol()
client_sock = protocol.makeSocket()
#client_sock.bind(client_addr)
filename = 'myfile_20.png'
#print("called threeway")
while protocol.threeWayConnect_receiver(client_sock,server_addr,wind_size,filename) == 0:
    print("Reconnecting")


print("sent to server")

newFile = f"client_{filename}"
recvFile(newFile,client_sock)

protocol.closeSocket(client_sock)