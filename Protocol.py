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
    def __init__(self):
        print("Reliable UDP Protocol Initiated")
        self.lockServer = threading.Lock()
        self.LockClient = threading.Lock()
        self.Acklock = threading.Lock()
        self.Ackread = 0
        self.Ackreadlock = threading.Lock()
        self.TriDuplock = threading.Lock()

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sock

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
            else:
                sock.sendto(message, address)
                timer = Thread(target=self.Timeout)
    

    def sendDataPackets(self, msg, sock, address):
        ''' 
        Array initalize for maintaing thread-packet mapping, size is  twice wndow_size
        ACK array-same size 0-not received, 1- received, 2 - retrans
        Triple-DUP ack array, intialized to 0, increment 1 when a corresponding next expected seq number received
        '''
        window_start = 0
        window_end = self.window_size-1
        AckArray = [0]*(2*self.window_size)
        TripleDUP = [0]*(2*self.window_size)
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
                seq = (seq+1)%2*self.window_size
                # count[0]+=1
            while count[0] == self.window_size:
                time+=1
            time=0
        return None



proto = Protocol()
sock = proto.create_socket()
sock.bind(('127.0.0.1', 6000))
data, address = sock.recvfrom(65555)
text = data.decode('ascii')
print('client at {} says {!r}'.format(address, text))
info = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed quis fringilla leo. Morbi ultricies lorem at leo elementum, quis volutpat nulla pellentesque. Fusce vel turpis ac turpis finibus dapibus vitae vel enim. Vivamus eleifend ac risus sit amet gravida. Sed tempus at odio quis commodo. Praesent imperdiet ligula non sem egestas ultrices. Vestibulum posuere leo eget tristique ullamcorper. Nulla non tortor consectetur, viverra lorem sed, lobortis nisl.Nullam in pretium nisi. Morbi pulvinar quis mauris porta interdum. Vivamus eu magna id leo mollis luctus. Aliquam egestas nec lorem vel efficitur. Sed et quam eu erat fringilla consectetur et id tortor. Ut placerat lorem et finibus pellentesque. Vestibulum a fermentum libero, quis ornare ligula. Suspendisse tempus nec arcu vel eleifend. Vestibulum viverra mi eros, eget lacinia risus elementum nec. Maecenas sed suscipit velit. Integer id justo fermentum orci imperdiet lobortis. Quisque vitae velit ut ligula aliquam commodo. Ut viverra maximus vulputate. Praesent volutpat dolor ligula, commodo tincidunt eros vehicula et.Nulla auctor non lacus eget rutrum. Ut id nibh elit. Mauris sed quam nisi. Duis in vestibulum dui. Ut vitae tincidunt enim, blandit gravida dolor. Praesent rhoncus, nisl ut rhoncus tempor, sapien est feugiat eros, non dapibus purus felis in mauris. Curabitur tempus mauris quis leo vestibulum, vel iaculis diam facilisis. Aliquam mattis odio ac dolor venenatis vulputate. Aenean ac eros sollicitudin, mattis nunc at, gravida urna. Donec consequat turpis quis tristique finibus. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Morbi sit amet ultricies orci. Aenean non posuere orci. Pellentesque nec nulla nec nunc congue consequat. Curabitur aliquam ipsum nec neque commodo, ut bibendum nunc ullamcorper.Vestibulum luctus, dui ac condimentum faucibus, nibh felis volutpat ante, vitae tincidunt lorem enim at sem. Maecenas egestas ac magna ut auctor. Duis nec pulvinar justo, vel laoreet dui. Nulla facilisi. Ut porta ipsum at magna faucibus, vitae congue ante laoreet. Praesent pellentesque efficitur sem sed volutpat. Suspendisse metus elit, dictum id mi vel, ultricies bibendum urna. Nam pulvinar dictum nunc sed sagittis. Vestibulum at molestie sapien. Morbi eros libero, consequat vel felis sed, convallis venenatis lectus. Mauris purus velit, sagittis a mi eget, lacinia euismod lectus. Phasellus molestie eleifend arcu, ut convallis ex ultrices id. Integer ultricies tempor arcu ac vulputate.Curabitur elit dui, cursus eget odio ac, rhoncus hendrerit nunc. Integer tortor nulla, tempus ac mi vitae, malesuada pulvinar sem. Fusce sit amet tincidunt arcu, nec fringilla nisi. Phasellus ut erat eu nulla vulputate aliquet sed at eros. Vestibulum ut pulvinar leo, in lobortis est. Curabitur convallis vel nunc vel ornare. Aliquam non lacinia tellus. Praesent nec risus euismod erat vehicula sagittis. Aenean sed massa varius, lobortis arcu in, commodo augue.@"
proto.sendDataPackets(info, sock, address)
# data = proto.makeDataPacket("hello", 0, 0, 0, 6)
# ack = proto.makeACKPacket(6, 3)
# print(data +"\n" + ack)

# def func(var):
#     var['four']=5

# var = {'four':4}
# func(var)
# print('The variable is ',var)