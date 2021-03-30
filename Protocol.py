import socket
import hashlib
from threading import Thread
import threading

class Protocol():
    delim = "<!>"
    msg_size = 200
    window_size=5
    def __init__(self):
        print("Reliable UDP Protocol Initiated")
        self.lockServer = threading.Lock()
        self.LockClient = threading.Lock()

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
        data, address = sock.recvfrom(65555)
        line = data.split('<!>')
        AckArray[line[0]]=1
        TripleDUP[line[0]]+=1
        return

    def ThreadSend(self):
        return

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
        while count[0] < self.window_size:
            time=0
            while(data_sent<length/self.msg_size and count[0]<self.window_size):
                data = msg[data_sent*self.msg_size:(data_sent+1)*self.msg_size]
                data = self.makeDataPacket(data, 0, 0, 0, seq)
                Thread(target=self.ThreadSend, args=(AckArray, TripleDUP, data, sock, address, count), name=seq).start() 
                seq = (seq+1)%2*self.window_size
                # count[0]+=1
            while count[0] == self.window_size:
                time+=1
            time=0
proto = Protocol()
data = proto.makeDataPacket("hello", 0, 0, 0, 6)
ack = proto.makeACKPacket(6, 3)
print(data +"\n" + ack)

# def func(var):
#     var['four']=5

# var = {'four':4}
# func(var)
# print('The variable is ',var)