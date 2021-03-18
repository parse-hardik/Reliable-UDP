import socket
import hashlib

class Protocol():
    def __init__(self):
        print("Reliable UDP Protocol Initiated")

    def create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sock

    def sendDataPacket(self, msg):
        msg = msg.encode()

# Protocol()