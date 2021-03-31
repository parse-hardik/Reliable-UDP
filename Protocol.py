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
        syn = self.makeDataPacket("Hello", self.window_size, 0, 0, 0)
        sock.sendto(syn.encode(), address)
        timer = Thread(target=self.Timeout)
        timer.start()
        while True:
            if not timer.is_alive():
                sock.sendto(syn.encode(), address)
                timer = Thread(target=self.Timeout)
                timer.start()
            else:
                data, address = sock.recvfrom(4096)
                data = data.decode('ascii')
                data = data.split(self.delim)
                if int(data[0])!=0 and int(data[1])!=0:
                    break
        
        ack = self.makeDataPacket(file_name_path, 0, 1, 0, -1)
        sock.sendto(ack.encode(), address)
        timer = Thread(target=self.Timeout)
        timer.start()
        while True:
            if not timer.is_alive():
                sock.sendto(ack.encode(), address)
                timer = Thread(target=self.Timeout)
                timer.start()
            else:
                data, address = sock.recvfrom(4096)
                data = data.decode('ascii')
                data = data.split(self.delim)
                if int(data[0])==-1 and int(data[1])==0:
                    return 1
        return -1

    def listen(self, sock):
        while True:
            data, address = sock.recvfrom(4096)
            data = data.decode('ascii')
            data = data.split(self.delim)
            if int(data[0])==0:
                continue
            self.window_size = int(data[0])
            synack = self.makeDataPacket("", 1, 1, 0, -1)
            sock.sendto(synack.encode(), address)
            timer = Thread(target=self.Timeout)
            timer.start()
            flag=0
            while True:
                if not timer.is_alive():
                    sock.sendto(synack.encode(), address)
                    timer = Thread(target=self.Timeout)
                    timer.start()
                else:
                    data, address = sock.recvfrom(4096)
                    data = data.decode('ascii')
                    if int(data[1])==1 and int(data[3])==-1:
                        self.file_to_send = data[4].decode('ascii')
                        flag=1
                        break
            if flag==1:
                break
        print('Received connection from {}'.format(address))
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
            self.Acklock.acquire()
            AckArray[int(line[0])]=1
            self.Acklock.release()
            TripleDUP[int(line[1])]+=1
            if TripleDUP[int(line[1])] >=3:
                self.Acklock.acquire()
                AckArray[int(line[1])]=2
                self.Acklock.release()
            if line[1][-1] =='.':
                break
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
            time=0
            while(data_sent < length/self.msg_size and count[0]<self.window_size):
                data = msg[data_sent*self.msg_size:(data_sent+1)*self.msg_size]
                data = self.makeDataPacket(data, 0, 0, 0, seq)
                Thread(target=self.ThreadSend, args=(AckArray, TripleDUP, data, sock, address, count, seq), name=seq).start() 
                data_sent+=1
                seq = (seq+1)%seq_window
                # count[0]+=1
            while count[0] == self.window_size:
                time+=1
            time=0
        return None

    def writeData(self, name, curr_seq_write, DataArray):
        while(curr_seq_write is not name):
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

        curr_seq_write = (curr_seq_write+1)%2*self.window_size



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
        curr_seq_write = [0] #current seq that needs to be written
        while True:
            data, address = sock.recvfrom(MAX_BYTES)
            text = data.decode('ascii')
            text = text.split('<!>')
            message_num = int(text[3])

            #if message not in given window
            if(not ((next_expec < self.recv_window_end and message_num >= next_expec and message_num<=self.recv_window_end) or (next_expec > self.recv_window_end and (message_num >= next_expec or message_num<=self.recv_window_end )))):
                continue
            
            original_message = text[4][2:-1]#check
            hashed_message = text[5][2:-1]#check

            #check if packet is corrupted or not
            check_hash = str(hashlib.sha1(original_message.encode()).hexdigest())
            if (check_hash is not hashed_message):
                continue

            #if not logic
            self.DataArraylock.acquire()
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
                window_end =  (window_end+1)%seq_window
            
            message = self.makeACKPacket(message_num,next_expec)
            message = message.encode()
            sock.sendto(message, address)

            if(original_message[-1]=='@'):
                break

        # Hello, I am invisible!
        return None



proto = Protocol()
proto.recvDataPackets()
# sock = proto.create_socket()
# sock.bind(('127.0.0.1', 6000))
# data, address = sock.recvfrom(65555)
# text = data.decode('ascii')
# print('client at {} says {!r}'.format(address, text))
# info = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed quis fringilla leo. Morbi ultricies lorem at leo elementum, quis volutpat nulla pellentesque. Fusce vel turpis ac turpis finibus dapibus vitae vel enim. Vivamus eleifend ac risus sit amet gravida. Sed tempus at odio quis commodo. Praesent imperdiet ligula non sem egestas ultrices. Vestibulum posuere leo eget tristique ullamcorper. Nulla non tortor consectetur, viverra lorem sed, lobortis nisl.Nullam in pretium nisi. Morbi pulvinar quis mauris porta interdum. Vivamus eu magna id leo mollis luctus. Aliquam egestas nec lorem vel efficitur. Sed et quam eu erat fringilla consectetur et id tortor. Ut placerat lorem et finibus pellentesque. Vestibulum a fermentum libero, quis ornare ligula. Suspendisse tempus nec arcu vel eleifend. Vestibulum viverra mi eros, eget lacinia risus elementum nec. Maecenas sed suscipit velit. Integer id justo fermentum orci imperdiet lobortis. Quisque vitae velit ut ligula aliquam commodo. Ut viverra maximus vulputate. Praesent volutpat dolor ligula, commodo tincidunt eros vehicula et.Nulla auctor non lacus eget rutrum. Ut id nibh elit. Mauris sed quam nisi. Duis in vestibulum dui. Ut vitae tincidunt enim, blandit gravida dolor. Praesent rhoncus, nisl ut rhoncus tempor, sapien est feugiat eros, non dapibus purus felis in mauris. Curabitur tempus mauris quis leo vestibulum, vel iaculis diam facilisis. Aliquam mattis odio ac dolor venenatis vulputate. Aenean ac eros sollicitudin, mattis nunc at, gravida urna. Donec consequat turpis quis tristique finibus. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Morbi sit amet ultricies orci. Aenean non posuere orci. Pellentesque nec nulla nec nunc congue consequat. Curabitur aliquam ipsum nec neque commodo, ut bibendum nunc ullamcorper.Vestibulum luctus, dui ac condimentum faucibus, nibh felis volutpat ante, vitae tincidunt lorem enim at sem. Maecenas egestas ac magna ut auctor. Duis nec pulvinar justo, vel laoreet dui. Nulla facilisi. Ut porta ipsum at magna faucibus, vitae congue ante laoreet. Praesent pellentesque efficitur sem sed volutpat. Suspendisse metus elit, dictum id mi vel, ultricies bibendum urna. Nam pulvinar dictum nunc sed sagittis. Vestibulum at molestie sapien. Morbi eros libero, consequat vel felis sed, convallis venenatis lectus. Mauris purus velit, sagittis a mi eget, lacinia euismod lectus. Phasellus molestie eleifend arcu, ut convallis ex ultrices id. Integer ultricies tempor arcu ac vulputate.Curabitur elit dui, cursus eget odio ac, rhoncus hendrerit nunc. Integer tortor nulla, tempus ac mi vitae, malesuada pulvinar sem. Fusce sit amet tincidunt arcu, nec fringilla nisi. Phasellus ut erat eu nulla vulputate aliquet sed at eros. Vestibulum ut pulvinar leo, in lobortis est. Curabitur convallis vel nunc vel ornare. Aliquam non lacinia tellus. Praesent nec risus euismod erat vehicula sagittis. Aenean sed massa varius, lobortis arcu in, commodo augue.@"
# proto.sendDataPackets(info, sock, address)
# data = proto.makeDataPacket("hello", 0, 0, 0, 6)
# ack = proto.makeACKPacket(6, 3)
# print(data +"\n" + ack)

# def func(var):
#     var['four']=5

# var = {'four':4}
# func(var)
# print('The variable is ',var)

