import socket
import hashlib

class Protocol():
    delim = "<!>"
    def __init__(self):
        print("Reliable UDP Protocol Initiated")

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
        data+=str(hashlib.sha1(info.encode()).hexdigest()) + self.delim
        return data

    def sendDataPacket(self, msg):
        msg = msg.encode()

proto = Protocol()
data = proto.makeDataPacket("hello", 0, 0, 0, 6)
print(data)