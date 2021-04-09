import socket
import hashlib
from threading import Thread
import time
import threading
import sys
import math
import os

class Protocol():
    delim = "<!>"
    msg_size = 5
    window_size = 5
    timeout_time = 1
    MAX_BYTES = 65555
    def __init__(self):
        print("Reliable UDP Protocol Initiated")
        self.Acklock = threading.Lock()
        self.Ackread = 0
        self.Ackreadlock = threading.Lock()
        self.windowlock = threading.Lock()
        self.DataArraylock = threading.Lock()
        self.senderThreadCountLock = threading.Lock()

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sock
        
    def connect(self, sock, address, window, file_name_path):
        # self.window_size = window
        print("Three way handshake initiated")
        syn = self.makeDataPacket("Hello", self.window_size, 0, 0, 0)
        sock.sendto(syn.encode(), address)
        sock.settimeout(self.timeout_time)
        while True:
            try:
                data, address = sock.recvfrom(4096)
            except socket.timeout as e:
                err = e.args[0]
                if err == 'timed out':
                    sock.sendto(syn.encode(), address)
                    continue
            data = data.decode('ascii')
            data = data.split(self.delim)
            if int(data[0])!=0 and int(data[1])!=0:
                break
        
        
        ack = self.makeDataPacket(file_name_path, 0, 1, 0, -1)
        sock.sendto(ack.encode(), address)
        sock.settimeout(None)
        print("Three way handshake successfull")
        return 1

    def listen(self, sock):
        flag=0
        while True:
            data, address = sock.recvfrom(4096)
            data = data.decode('ascii')
            data = data.split(self.delim)
            if int(data[0])==0:
                continue
            self.window_size = int(data[0])
            synack = self.makeDataPacket("", 1, 1, 0, -1)
            sock.sendto(synack.encode(), address)
            sock.settimeout(self.timeout_time)
            while True:
                try:
                    data, address = sock.recvfrom(4096)
                    
                except socket.timeout as e:
                    err = e.args[0]
                    if err == 'timed out':
                        sock.sendto(synack.encode(), address)
                        continue
                data = data.decode('ascii')
                data = data.split(self.delim)
                if int(data[1])==1 and int(data[3])==-1:
                    self.file_to_send = data[4][2:-1]
                    check = str(hashlib.sha1(self.file_to_send.encode()).hexdigest())
                    if check!=data[5]:
                        break
                    flag=1
                    break
            if flag==1:
                break
            
        sock.settimeout(None)
        print('Received connection from {} and is requesting {}'.format(address, self.file_to_send))
        return self.file_to_send, address

    def close(self, sock, address):
        print("Socket closing initiated")
        fin = self.makeDataPacket("Close", 0, 0, 1, 0)
        sock.sendto(fin.encode(), address)
        sock.settimeout(self.timeout_time)
        while True:
            try:
                data, address = sock.recvfrom(4096)
            except socket.timeout as e:
                err = e.args[0]
                if err == 'timed out':
                    sock.sendto(fin.encode(), address)
                    continue
            data = data.decode('ascii')
            
            data = data.split('<!>')
            print(data)
            if len(data)>2 and int(data[2])!=0 and int(data[1])!=0:
                break
        
        
        ack = self.makeDataPacket("Closing", 0, 1, 0, -1)
        sock.sendto(ack.encode(), address)
        sock.settimeout(None)
        print("Socket closing successful")
        return 1

    def closeConn(self, sock, address):
        finack = self.makeDataPacket("FIN-ACK", 0, 1, 1, 0)
        sock.sendto(finack.encode(), address)
        sock.settimeout(self.timeout_time)
        while True:
            try:
                data, address = sock.recvfrom(4096)
            except socket.timeout as e:
                err = e.args[0]
                if err == 'timed out':
                    sock.sendto(finack.encode(), address)
                    continue
            data = data.decode('ascii')
            data = data.split(self.delim)
            if int(data[3])==-1 and int(data[1])!=0:
                break
        return None

    def makeDataPacket(self, info, SYN, ACK, FIN, seq):
        data=""
        data+=str(SYN) + self.delim
        data+=str(ACK) + self.delim
        data+=str(FIN) + self.delim
        data+=str(seq) + self.delim
        data+=str(info.encode('ascii')) + self.delim
        data+=str(hashlib.sha1(info.encode()).hexdigest())
        return data

    def makeACKPacket(self, ACK, seq):
        data=""
        data+=str(ACK) + self.delim
        data+=str(seq)
        return data

    def recvACK(self, AckArray, TripleDUP, sock, num_packets, count):
        ''' 
        If lock on both: As we receive ack, put it in the ACK list, and increment corresponding next expected seq number in
        TripleDUP list 
        '''
        address = 0

        seq_window = 2*self.window_size

        while True:
            data, address = sock.recvfrom(65555)
            data = data.decode('ascii')
            line = data.split('<!>')
            print(line)

            packet_num = int(line[0])
            next_expec = int(line[1])
            
            print(f"Packet {packet_num} in current window from {self.sender_window_start} to {self.sender_window_end}")


            #check if within the window
            if(not ((self.sender_window_start < self.sender_window_end and packet_num >= self.sender_window_start and packet_num <= self.sender_window_end) or (self.sender_window_start > self.sender_window_end and (packet_num >= self.sender_window_start or packet_num <= self.sender_window_end)) )):
                # print(f"Packet {packet_num} does not belong to current window from {self.sender_window_start} to {self.sender_window_end}")
                continue

            # Mark Ack received from window start to next_expec
            cpy = self.sender_window_start
            self.Acklock.acquire()
            print(AckArray,"before")
            while(cpy != next_expec):
                if cpy == packet_num:
                    cpy = (cpy+1)%seq_window
                    continue
                if(AckArray[cpy]!=1 and AckArray[cpy]!=4):
                    AckArray[cpy] = 1
                    num_packets-=1
                cpy = (cpy+1)%seq_window
                # print(cpy, next_expec)
            print(AckArray ,"for packet",{packet_num},self.sender_window_start, next_expec)
            print(cpy,self.sender_window_start)
            self.Acklock.release()


            #got Ack again
            if(AckArray[packet_num]!=1 and AckArray[packet_num] !=4):
                self.Acklock.acquire()
                AckArray[packet_num]=1
                self.Acklock.release()
                # print(f"\n\ngot Ack for {packet_num}")
                print(AckArray)
                num_packets-=1
                print(packet_num, num_packets)

            while(AckArray[self.sender_window_start]==4 or AckArray[self.sender_window_start]==1 ):
                
                while(AckArray[self.sender_window_start]==1):
                    pass

                self.Acklock.acquire()
                AckArray[self.sender_window_start]=0
                self.Acklock.release()

                TripleDUP[self.sender_window_start]=0

                self.windowlock.acquire()
                self.sender_window_start = (self.sender_window_start+1)%seq_window
                self.sender_window_end = (self.sender_window_end+1)%seq_window
                self.windowlock.release()

                

            print(f"window size {self.sender_window_start} to {self.sender_window_end}")
            # print(f"updated ACK array {AckArray}")
            TripleDUP[next_expec]+=1
            # print(f"updated Triple DUP {TripleDUP}")
            if TripleDUP[next_expec] >=3:
                self.Acklock.acquire()
                AckArray[next_expec]=2
                TripleDUP[next_expec]=0
                self.Acklock.release()
            
            if (num_packets == 0) :
                # print(packet_num, num_packets)
                break
            '''
            To implement end of recieving ACKs and stop the server using break
            '''
        self.close(sock, address)
        return

    def Timeout(self):
        time.sleep(2)
        return None

    def ThreadSend(self, AckArray, TripleDUP, message, sock, address, count , name):
        self.senderThreadCountLock.acquire()
        count[0]+=1
        self.senderThreadCountLock.release()
        message = message.encode()
        sock.sendto(message, address)
        timer = Thread(target=self.Timeout)
        timer.start()
        while True :
            if(timer.is_alive()):
                
                status = AckArray[name]

                if(status==1) :
                    self.Acklock.acquire()
                    AckArray[name] = 4
                    self.Acklock.release()
                    return None
                
                #triple dup retransmission
                elif (status == 2) : 
                    sock.sendto(message, address)
                    print(f"Triple dup sending {name} ")
                    timer = Thread(target=self.Timeout)
                    timer.start()
            else:
                sock.sendto(message, address)
                print(f"timeout sending  {message} ")
                timer = Thread(target=self.Timeout)
                timer.start()

    def sendFile(self, sock, address, file):

        if os.path.exists("output.txt"):
            os.remove("output.txt")

        f = open(file, "r")
        msg = f.read()
        # msg=""
        # while True:
        #     line=f.readline()
        #     if not line:
        #         break
        #     msg+=line[0:-1] + " "
        f.close()
        # print(msg,"hii")
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
        data_sent = 0
        length = len(msg)
        num_packets = math.ceil(length/self.msg_size)
        self.sender_window_start = 0
        self.sender_window_end = self.window_size-1

        #managing sending window
        seq=0
        seq_start = 0

        count=[0]
        Thread(target=self.recvACK, args=(AckArray, TripleDUP, sock, num_packets, count)).start()

        #first window 
        while(data_sent < length/self.msg_size and count[0]<self.window_size):
            print(f"sending {seq} ")
            data = msg[data_sent*self.msg_size:(data_sent+1)*self.msg_size]
            data = self.makeDataPacket(data, 0, 0, 0, seq)
            Thread(target=self.ThreadSend, args=(AckArray, TripleDUP, data, sock, address, count, seq), name=seq).start() 
            data_sent+=1
            seq = (seq+1)%seq_window
            # time.sleep(0.01)
        #later transmissions
        while data_sent < length/self.msg_size:
            
            self.windowlock.acquire()
            window_st = self.sender_window_start
            window_end = self.sender_window_end
            self.windowlock.release()

            while data_sent < length/self.msg_size and (seq_start < window_st or (window_st < window_end and seq_start > window_end)):
                print(f"sending {seq} for window {window_st} to {window_end}")
                print(f"{seq_start} prev start to {window_st}")
                data = msg[data_sent*self.msg_size:(data_sent+1)*self.msg_size]
                data = self.makeDataPacket(data, 0, 0, 0, seq)
                Thread(target=self.ThreadSend, args=(AckArray, TripleDUP, data, sock, address, count, seq), name=seq).start() 
                data_sent+=1
                seq = (seq+1)%seq_window
                seq_start = (seq_start+1)%seq_window


            
            
        return None

    def writeData(self, name, curr_seq_write, DataArray):
        while(curr_seq_write[0] != name):
            pass

        self.DataArraylock.acquire()
        msg = DataArray[name]
        DataArray[name] = ""
        self.DataArraylock.release()

        output_file = open("output.txt",'a')
        output_file.write(msg)
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
        sock.settimeout(40)
        last_sent = 0
        while True:
            try:
                data, address = sock.recvfrom(4096)
            except socket.timeout as e:
                err = e.args[0]
                if err == 'timed out':
                    print(next_expec,info)
                    return info
            
            info = True
            text = data.decode('ascii')
            text = text.split('<!>')
            # print(text)
            

            #Fin bit received
            if(int(text[2])==1):
                self.closeConn(sock, address)
                return info

            message_num = int(text[3])
            if message_num==-1:
                continue
            print(f"got a packet {message_num} in window {next_expec} {self.recv_window_end} ")

            #if message not in given window
            if(not ((next_expec < self.recv_window_end and message_num >= next_expec and message_num<=self.recv_window_end) or (next_expec > self.recv_window_end and (message_num >= next_expec or message_num<=self.recv_window_end )))):
                # print(f"got a packet {message_num} not within window {next_expec} {self.recv_window_end} ")
                message = self.makeACKPacket(last_sent,next_expec)
                message = message.encode()
                sock.sendto(message, address)
                print(message)
                continue
            
            original_message = text[4][2:-1]
            hashed_message = text[5]

            #check if packet is corrupted or not
            check_hash = str(hashlib.sha1(original_message.encode()).hexdigest())

            if (check_hash != hashed_message):
                message = self.makeACKPacket(last_sent,next_expec)
                message = message.encode()
                sock.sendto(message, address)
                print(message)
                continue

            #if not logic
            self.DataArraylock.acquire()
            if(DataArray[message_num] == ""):
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
            last_sent = message_num
            message = self.makeACKPacket(message_num,next_expec)
            message = message.encode()
            print(f"sending {message}")
            sock.sendto(message, address)
        return None
