import socket
import hashlib
from threading import Thread
import time
import threading

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
        self.TriDuplock = threading.Lock()
        self.DataArraylock = threading.Lock()

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sock

    def connect(self, sock, address, window, file_name_path):
        self.window_size = window
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
            data = data.split(self.delim)
            if int(data[2])!=0 and int(data[1])!=0:
                break
        
        
        ack = self.makeDataPacket("Closing", 0, 1, 0, -1)
        sock.sendto(ack.encode(), address)
        sock.settimeout(None)
        print("Socket closing successfull")
        return 1

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

    def recvACK(self, AckArray, TripleDUP, sock):
        ''' 
        If lock on both: As we receive ack, put it in the ACK list, and increment corresponding next expected seq number in
        TripleDUP list 
        '''
        #check if within window
        while True:
            data, address = sock.recvfrom(65555)
            data = data.decode('ascii')
            line = data.split('<!>')
            print(line)
            self.Acklock.acquire()
            AckArray[int(line[0])]=1
            print(AckArray)
            self.Acklock.release()
            TripleDUP[int(line[1])]+=1
            if TripleDUP[int(line[1])] >=3:
                self.Acklock.acquire()
                AckArray[int(line[1])]=2
                self.Acklock.release()
            # if line[1][-1] =='.':
            #     break
            '''
            To implement end of recieving ACKs and stop the server using break
            '''
        return

    def Timeout(self):
        time.sleep(self.timeout_time)
        return None

    def ThreadSend(self, AckArray, TripleDUP, message, sock, address, count , name):
        count[0]+=1
        message = message.encode()
        sock.sendto(message, address)
        timer = Thread(target=self.Timeout)
        timer.start()
        while True :
            if(timer.is_alive()):

                self.Ackreadlock.acquire()
                if(not self.Ackread):
                    self.Acklock.acquire()
                self.Ackread+=1
                self.Ackreadlock.release()

                status = AckArray[name]

                self.Ackreadlock.acquire()
                self.Ackread-=1

                if(not self.Ackread):
                    self.Acklock.release()
                
                self.Ackreadlock.release()

                if(status==1) :
                    count[0]-=1
                    return None
                elif (status == 2) : #triple dup retransmission
                    #check do I need to kill prev thread
                    sock.sendto(message, address)
                    timer = Thread(target=self.Timeout)
                    timer.start()
            else:
                sock.sendto(message, address)
                timer = Thread(target=self.Timeout)
                timer.start()

    def sendDataPackets(self, msg, sock, address):
        ''' 
        Array initalize for maintaing thread-packet mapping, size is  twice wndow_size
        ACK array-same size 0-not received, 1- received, 2 - retrans
        Triple-DUP ack array, intialized to 0, increment 1 when a corresponding next expected seq number received
        '''
        self.sender_window_start = 0
        seq_window = 2*self.window_size
        self.sender_window_end = self.window_size-1
        AckArray = [0]*seq_window
        TripleDUP = [0]*seq_window
        data_sent = 0
        length = len(msg)
        seq=0
        count=[0]
        Thread(target=self.recvACK, args=(AckArray, TripleDUP, sock)).start()
        while count[0] < self.window_size and data_sent < length/self.msg_size:
            while(data_sent < length/self.msg_size and count[0]<self.window_size):
                data = msg[data_sent*self.msg_size:(data_sent+1)*self.msg_size]
                data = self.makeDataPacket(data, 0, 0, 0, seq)
                Thread(target=self.ThreadSend, args=(AckArray, TripleDUP, data, sock, address, count, seq), name=seq).start() 
                data_sent+=1
                seq = (seq+1)%seq_window
            while count[0] == self.window_size:
                pass
        return None

    def writeData(self, name, curr_seq_write, DataArray):
        while(curr_seq_write[0] != name):
            pass

        self.DataArraylock.acquire()
        msg = DataArray[name]
        self.DataArraylock.release()

        output_file = open("output.txt",'a')
        output_file.write(msg)
        output_file.close()

        self.DataArraylock.acquire()
        DataArray[name] = ""
        self.DataArraylock.release()

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
        sock.settimeout(2)
        while True:
            try:
                data, address = sock.recvfrom(4096)
            except socket.timeout as e:
                err = e.args[0]
                if err == 'timed out':
                    return info
            info = True
            text = data.decode('ascii')
            text = text.split('<!>')
            message_num = int(text[3])

            #if message not in given window
            if(not ((next_expec < self.recv_window_end and message_num >= next_expec and message_num<=self.recv_window_end) or (next_expec > self.recv_window_end and (message_num >= next_expec or message_num<=self.recv_window_end )))):
                continue
            
            original_message = text[4][2:-1]
            hashed_message = text[5]

            #check if packet is corrupted or not
            check_hash = str(hashlib.sha1(original_message.encode()).hexdigest())

            if (check_hash != hashed_message):
                continue

            #if not logic
            self.DataArraylock.acquire()
            if(DataArray[message_num] !=""):
                continue
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
            
            message = self.makeACKPacket(message_num,next_expec)
            message = message.encode()
            sock.sendto(message, address)
        return None
