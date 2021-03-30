import socket
import hashlib
from threading import Thread
import time

class Protocol():
    delim = "<!>"
    msg_size = 200
    window_size = 5
    timeout_time = 1
    def __init__(self):
        print("Reliable UDP Protocol Initiated")
        self.lockServer = threading.Lock()
        self.LockClient = threading.Lock()
        self.Acklock = threading.Lock()
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

    def recvACK(self, ACK, TripleDUP):
        ''' 
        If lock on both: As we receive ack, put it in the ACK list, and increment corresponding next expected seq number in
        TripleDUP list 
        '''
        return

    def Timeout(self):
        time.sleep(timeout_time)
        return None

    def ThreadSend(self, AckArray, TripleDUP, message, sock, address, count , name):
        count[0]+=1
        sock.sendto(message, address)
        timer = Thread(target=self.Timeout)
        while True :
            if(timer.is_alive()):
                while self.Acklock.locked():
                    a=1
                status = AckArray[name]
                if(status==1) :
                    count[0]-=1
                    return None
                else if (status == 2) : #triple dup retransmission
                    #check do I need to kill prev thread
                    sock.sendto(message, address)
                    timer = Thread(target=self.Timeout)
            else:
                sock.sendto(message, address)
                timer = Thread(target=self.Timeout)
    

    def sendDataPackets(self, msg):
        ''' 
        Array initalize for maintaing thread-packet mapping, size is  twice wndow_size
        ACK array-same size 0-not received, 1- received, 2 - retrans
        Triple-DUP ack array, intialized to 0, increment 1 when a corresponding next expected seq number received
        '''
        window_start = 0
        window_end = self.window_size-1
        arrThread = []
        AckArray = []
        TripleDUP = []
        for i in 2*window_size:
            arrThread[i] = Thread(target=self.ThreadSend, args=(AckArray, TripleDUP), name=i)
        msg = msg.encode()

proto = Protocol()
data = proto.makeDataPacket("hello", 0, 0, 0, 6)
ack = proto.makeACKPacket(6, 3)
print(data +"\n" + ack)

# def func(var):
#     var['four']=5

# var = {'four':4}
# func(var)
# print('The variable is ',var)