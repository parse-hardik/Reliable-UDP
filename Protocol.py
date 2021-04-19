import socket
import hashlib
from threading import Thread
import time
import threading
import sys
import math
import os
import datetime
import base64


class Protocol():
    delim = "<!>"
    msg_size = 1024
    window_size = 8
    timeout_time = 1
    data_packet_timeout = 0.5
    MAX_BYTES = 5000000
    closing_connection_timeout = 5
    reinitiate_handshake_timeout = 5
    max_retransmission = 100
    req_file=""
    data_size = 0
    max_rt = 0

    def __init__(self):
        print("Reliable UDP Protocol Initiated")
        self.Acklock = threading.Lock()
        self.windowlock = threading.Lock()
        self.DataArraylock = threading.Lock()
        self.senderThreadCountLock = threading.Lock()
        self.packetLeft = threading.Lock()
        self.retransmission_stop = False

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sock
        
    def connect(self, sock, address, window, file_name_path):
        self.window_size = window
        if os.path.exists("output_"+file_name_path):
            os.remove("output_"+file_name_path)
        self.req_file = file_name_path
        print("Three way handshake initiated")
        syn = self.makeDataPacket("Hello", self.window_size, 0, 0, 0)
        sock.sendto(bytes(syn.encode()), address)
        sock.settimeout(self.timeout_time)
        while True:
            try:
                data, address = sock.recvfrom(self.MAX_BYTES)
            except socket.timeout as e:
                err = e.args[0]
                if err == 'timed out':
                    sock.sendto(bytes(syn.encode()), address)
                    continue
            data = data.decode()
            data = data.split(self.delim)
            if int(data[0])!=0 and int(data[1])!=0:
                break
        
        ack = self.makeDataPacket(file_name_path, 0, 1, 0, -1)
        sock.sendto(bytes(ack.encode()), address)
        sock.settimeout(None)
        print("Three way handshake successfull")
        return 1

    def listen(self, sock):
        flag=0
        while True:
            data, address = sock.recvfrom(self.MAX_BYTES)
            print(f"Got a connection request from {address}")
            data = data.decode()
            data = data.split(self.delim)
            if int(data[0])==0:
                continue
            self.window_size = int(data[0])
            synack = self.makeDataPacket("", 1, 1, 0, -1)
            sock.sendto(bytes(synack.encode()), address)
            sock.settimeout(self.timeout_time)
            while True:
                try:
                    data, address = sock.recvfrom(self.MAX_BYTES)
                    
                except socket.timeout as e:
                    err = e.args[0]
                    if err == 'timed out':
                        sock.sendto(bytes(synack.encode()), address)
                        print("synack")
                        continue
                data = data.decode()
                data = data.split(self.delim)
                # if int(data[1])==-1 and int(data[3])==0:
                if int(data[1])==1 and int(data[3])==-1:
                    self.file_to_send = data[4]
                    check = str(hashlib.sha1(self.file_to_send.encode()).hexdigest())
                    if check!=data[5]:
                        break
                    flag=1
                    break
            if flag==1:
                break
            
        sock.settimeout(None)
        print('Connection {} is requesting {}'.format(address, self.file_to_send))
        return self.file_to_send, address

    def close(self, sock, address):
        print("Socket closing initiated")
        fin = self.makeDataPacket("Close", 0, 0, 1, 0)
        sock.sendto(bytes(fin.encode()), address)
        print("FIN")
        sock.settimeout(self.timeout_time)
        while True:
            try:
                data, address = sock.recvfrom(self.MAX_BYTES)
            except socket.timeout as e:
                err = e.args[0]
                if err == 'timed out':
                    sock.sendto(bytes(fin.encode()), address)
                    continue
            data = data.decode() 
            data = data.split('<!>')
            print("FIN-ACK")
            if len(data)>2 and int(data[2])!=0 and int(data[1])!=0:
                break
        
        
        ack = self.makeDataPacket("Closing", 0, 1, 0, -1)
        sock.sendto(bytes(ack.encode()), address)
        print("ACK")
        # sock.settimeout(None)
        print("Socket closing successful")
        return 1

    def closeConn(self, sock, address):
        print("FIN")
        finack = self.makeDataPacket("FIN-ACK", 0, 1, 1, 0)
        sock.sendto(bytes(finack.encode()), address)
        print("FIN-ACK")
        sock.settimeout(self.timeout_time)
        while True:
            try:
                data, address = sock.recvfrom(self.MAX_BYTES)
            except socket.timeout as e:
                err = e.args[0]
                if err == 'timed out':
                    sock.sendto(bytes(finack.encode()), address)
                    continue
            data = data.decode()
            data = data.split(self.delim)
            print("ACK")
            if int(data[3])==-1 and int(data[1])!=0:
                break
        print("Connection closed!")
        return None

    def makeDataPacket(self, info, SYN, ACK, FIN, seq):
        data=""
        data+=str(SYN) + self.delim
        data+=str(ACK) + self.delim
        data+=str(FIN) + self.delim
        data+=str(seq) + self.delim
        data+=str(info) + self.delim
        data+=str(hashlib.sha1(info.encode()).hexdigest())
        return data

    def makeACKPacket(self, ACK, seq):
        data=""
        data+=str(ACK) + self.delim
        data+=str(seq)
        return data

    def recvACK(self, AckArray, TripleDUP, sock, num_packets, count, name):
        ''' 
        If lock on both: As we receive ack, put it in the ACK list, and increment corresponding next expected seq number in
        TripleDUP list 
        '''
        address = 0
        seq_window = 2*self.window_size

        sock.settimeout(1)

        while True:
            try:
                if(sock):
                    data, address = sock.recvfrom(self.MAX_BYTES)
                else :
                    break
            except socket.timeout as e:
                err = e.args[0]
                if err == 'timed out':
                    if (num_packets[0] <= 0) :
                        break
                    if(self.retransmission_stop):
                        break
                    continue

            if (num_packets[0] <= 0) :
                break
            if(self.retransmission_stop):
                break
            data = data.decode()
            line = data.split('<!>')
            # print(line)

            packet_num = int(line[0])
            next_expec = int(line[1])
            
            # print(f"{datetime.datetime.now().time()} : Packet {packet_num} in current window from {self.sender_window_start} to {self.sender_window_end} in {name}")


            #check if within the window
            if(not ((self.sender_window_start < self.sender_window_end and packet_num >= self.sender_window_start and packet_num <= self.sender_window_end) or (self.sender_window_start > self.sender_window_end and (packet_num >= self.sender_window_start or packet_num <= self.sender_window_end)) )):
            #     # print(f"Packet {packet_num} does not belong to current window from {self.sender_window_start} to {self.sender_window_end}")
                continue

            # Mark Ack received from window start to next_expec
            cpy = self.sender_window_start
            self.Acklock.acquire()
            while(cpy != next_expec):
                if cpy == packet_num:
                    cpy = (cpy+1)%seq_window
                    continue
                if(AckArray[cpy]!=1 and AckArray[cpy]!=4 and AckArray[cpy]!=5 ):
                    AckArray[cpy] = 1
                    self.packetLeft.acquire()
                    num_packets[0]-=1
                    self.packetLeft.release()
                cpy = (cpy+1)%seq_window
            self.Acklock.release()


            #got Ack again
            self.Acklock.acquire()
            if(AckArray[packet_num]!=1 and AckArray[packet_num] !=4 and AckArray[packet_num] !=5):
                AckArray[packet_num]=1
                self.packetLeft.acquire()
                num_packets[0]-=1
                self.packetLeft.release()
            self.Acklock.release()

            print(packet_num, num_packets[0], f" current window from {self.sender_window_start} to {self.sender_window_end}")
            # print(f"updated ACK array {AckArray}")

            self.windowlock.acquire()
            while(AckArray[self.sender_window_start]==4 or AckArray[self.sender_window_start]==1 ):
                
                while(AckArray[self.sender_window_start]==1):
                    pass

                self.Acklock.acquire()
                AckArray[self.sender_window_start]=5
                self.Acklock.release()

                TripleDUP[self.sender_window_start]=0

                
                self.sender_window_start = (self.sender_window_start+1)%seq_window
                self.sender_window_end = (self.sender_window_end+1)%seq_window
            self.windowlock.release()

                

            # print(f"{datetime.datetime.now().time()} : window size {self.sender_window_start} to {self.sender_window_end}")
            # print(f"updated ACK array {AckArray}")
            TripleDUP[next_expec]+=1
            # print(f"updated Triple DUP {TripleDUP}")
            if TripleDUP[next_expec] >=3:
                self.Acklock.acquire()
                if(AckArray[next_expec] == 0):
                    AckArray[next_expec]=2
                self.Acklock.release()
                TripleDUP[next_expec]=0
            
            if (num_packets[0] <= 0):
                break
            if(self.retransmission_stop):
                break
            '''
            To implement end of recieving ACKs and stop the server using break
            '''
        return None

    def Timeout(self):
        time.sleep(self .data_packet_timeout)
        return None

    def ThreadSend(self, AckArray, TripleDUP, message, sock, address, count , name, retransmission):
        self.senderThreadCountLock.acquire()
        count[0]+=1
        self.senderThreadCountLock.release()
        message = message.encode()
        message = bytes(message)
        sock.sendto(message, address)
        # st_time = time.time()
        timer = Thread(target=self.Timeout)
        timer.start()
        retransmission[name]=1
        while True :
            self.max_rt = max(self.max_rt, retransmission[name])
            if(self.retransmission_stop):
                return None
            if(timer.is_alive()):
                if(retransmission[name] >= self.max_retransmission):
                    self.retransmission_stop = True
                    return None

                status = AckArray[name]

                if(status==1) :
 
                    self.Acklock.acquire()
                    AckArray[name] = 4
                    self.Acklock.release()
                    return None
                
                #triple dup retransmission
                elif (status == 2) : 
                    sock.sendto(message, address)
                    # print(f"{datetime.datetime.now().time()} : Triple dup sending {name} in current window from {self.sender_window_start} to {self.sender_window_end} in {name}")
                    retransmission[name]+=1
                    timer = Thread(target=self.Timeout)
                    timer.start()
                    # st_time = time.time()
            else:
                sock.sendto(message, address)

                timer = Thread(target=self.Timeout)
                retransmission[name]+=1
                # st_time = time.time()
                timer.start()
                # print(f"{datetime.datetime.now().time()} : timeout sending  {name} in current window from {self.sender_window_start} to {self.sender_window_end} in {name}")

    def sendFile(self, sock, address, file):
        self.data_size = os.path.getsize(file)
        f = open(file, "rb")
        msg = base64.b64encode(f.read())
        f.close()
        self.sendDataPackets(msg, sock, address)
        return None

    def sendDataPackets(self, msg, sock, address):
        ''' 
        Array initalize for maintaing thread-packet mapping, size is  twice wndow_size
        ACK array-same size 0-not received, 1- received, 2 - retrans
        Triple-DUP ack array, intialized to 0, increment 1 when a corresponding next expected seq number received
        '''
        
        seq_window = 2*self.window_size
        AckArray = [0]*seq_window
        TripleDUP = [0]*seq_window
        retransmission = [0]*seq_window
        data_sent = 0
        length = len(msg)
        num_packets = [math.ceil(length/self.msg_size)]
        self.sender_window_start = 0
        self.sender_window_end = self.window_size-1

        #managing sending window
        seq=0
        seq_start = 0

        count=[0]
        ackThreads=[]

        #first window 
        print("\n\nSending File....\n")
        print("Number of packets",num_packets[0])

        for i in range(0,5):
            t = Thread(target=self.recvACK, args=(AckArray, TripleDUP, sock, num_packets, count, seq))
            t.start()
            ackThreads.append(t)


        start_time = time.time()
        while(data_sent < length/self.msg_size and count[0]<self.window_size):
            # print(f"{datetime.datetime.now().time()} : sending {seq} ")
            data = msg[data_sent*self.msg_size:(data_sent+1)*self.msg_size]
            data = self.makeDataPacket(data.decode(), 0, 0, 0, seq)
            Thread(target=self.ThreadSend, args=(AckArray, TripleDUP, data, sock, address, count, seq, retransmission), name=seq).start() 
            
            data_sent+=1
            seq = (seq+1)%seq_window
            # time.sleep(0.001)

        #later transmissions
        while data_sent < length/self.msg_size:
            self.windowlock.acquire()
            window_st = self.sender_window_start
            window_end = self.sender_window_end
            self.windowlock.release()

            while data_sent < length/self.msg_size and (seq_start < window_st or (window_st < window_end and seq_start > window_end)):
                # print(f"{datetime.datetime.now().time()} : sending {seq} for window {window_st} to {window_end}")
                # print(f"{datetime.datetime.now().time()} : {seq_start} prev start to {window_st}")
                data = msg[data_sent*self.msg_size:(data_sent+1)*self.msg_size]
                data = self.makeDataPacket(data.decode(), 0, 0, 0, seq)

                self.Acklock.acquire()
                AckArray[seq] = 0
                retransmission[seq] = 0
                self.Acklock.release()

                Thread(target=self.ThreadSend, args=(AckArray, TripleDUP, data, sock, address, count, seq, retransmission), name=seq).start() 
                data_sent+=1
                seq = (seq+1)%seq_window
                seq_start = (seq_start+1)%seq_window
                time.sleep(0.01)
        
        for t in ackThreads:
            t.join()
        
        end_time = time.time()
        print("File sent successfully!\n\n")
        print("------------Stats------------\n")
        print("Size of file sent", self.data_size,"bytes")
        print("Time required", end_time-start_time ,"seconds")
        print("Throughput", self.data_size/(end_time-start_time),"bytes/sec")
        print("Max retransmission",self.max_rt)
        print("\n\n-----------------------------\n")
        self.close(sock, address)

        return None

    def writeData(self, name, curr_seq_write, DataArray):
        while(curr_seq_write[0] != name):
            pass

        self.DataArraylock.acquire()
        msg = DataArray[name]
        DataArray[name] = ""
        self.DataArraylock.release()

        output_file = open("output_"+self.req_file,'ab')
        output_file.write(base64.b64decode(msg))
        output_file.close()

        seq_window = 2*self.window_size
        curr_seq_write[0] = (curr_seq_write[0]+1)%(seq_window)

        return None

    def recvDataPackets(self, address, sock):
        ''' 
        Initial seq num is 0
        Recieve packets and put them in data array(list of strings- size same as seq numbers)
        Check if the current packet is already 
        '''
        
        seq_window = 2*self.window_size
        DataArray = [""]*seq_window
        next_expec = 0
        self.recv_window_end = self.window_size - 1
        info = False
        curr_seq_write = [0] #current seq that needs to be written
        sock.settimeout(self.reinitiate_handshake_timeout)
        last_sent = 0
        while True:
            try:
                data, address = sock.recvfrom(self.MAX_BYTES)
                sock.settimeout(self.closing_connection_timeout)
            except socket.timeout as e:
                err = e.args[0]
                if err == 'timed out':
                    print(next_expec,info)
                    return info
            
            info = True
            text = data.decode()
            text = text.split('<!>')
            
            #Fin bit received
            if(int(text[2])==1):
                self.closeConn(sock, address)
                return info

            message_num = int(text[3])
            if message_num==-1:
                continue
            print(f"{datetime.datetime.now().time()} : got a packet {message_num} in window {next_expec} {self.recv_window_end} ")
            #if message not in given window
            if(not ((next_expec < self.recv_window_end and message_num >= next_expec and message_num<=self.recv_window_end) or (next_expec > self.recv_window_end and (message_num >= next_expec or message_num<=self.recv_window_end )))):
                # print(f"{datetime.datetime.now().time()} : got a packet {message_num} not within window {next_expec} {self.recv_window_end} ")
                message = self.makeACKPacket(last_sent,next_expec)
                message = message.encode()
                message = bytes(message)
                sock.sendto(message, address)
                # print(message)
                continue
            
            original_message = text[4]
            hashed_message = text[5]

            #check if packet is corrupted or not
            check_hash = str(hashlib.sha1(original_message.encode()).hexdigest())

            if (check_hash != hashed_message):
                message = self.makeACKPacket(last_sent,next_expec)
                message = message.encode()
                message = bytes(message)
                sock.sendto(message, address)
                # print("got wrong message", message)
                continue

            #if not logic
            self.DataArraylock.acquire()
            if(DataArray[message_num] == ""):
                last_sent = message_num
                DataArray[message_num] = original_message
                self.DataArraylock.release()

                while True:
                    self.DataArraylock.acquire()
                    next_string = DataArray[next_expec]
                    self.DataArraylock.release()

                    if(next_string==""):
                        break
                    
                    Thread(target=self.writeData, args=(next_expec, curr_seq_write, DataArray)).start()
                    next_expec = (next_expec+1)%seq_window
                    self.recv_window_end =  (self.recv_window_end+1)%seq_window
            
            else :
                self.DataArraylock.release()
            # last_sent = message_num
            message = self.makeACKPacket(message_num,next_expec)
            message = message.encode()
            message = bytes(message)
            sock.sendto(message, address)
            # print(f"{datetime.datetime.now().time()} : sending {message}")
        return None
