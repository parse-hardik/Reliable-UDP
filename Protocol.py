import socket
import hashlib

class Protocol():
    separator = "**!**"
    seq = 0
    seqlimit = 1
    def __init__(self):
        print("Reliable UDP Protocol Initiated")

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sock

    def handhake(self):
        

    def createDataPacket(self, msg, ack, syn, fin):
        checksum = hashlib.sha1(msg.encode()).hexdigest()
        data = str(self.seq) + self.separator + str(len(msg)) + self.separator + str(msg) + self.separator + str(checksum) + self.separator + str(syn) + self.separator + str(ack) + self.separator + str(fin)
        return data

# Protocol()