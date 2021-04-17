from Protocol import Protocol
import argparse

def client(address):
    proto = Protocol()
    sock = proto.create_socket()
    sock.bind(('localhost', 5000))
    recv = False
    while not recv:
        proto.connect(sock, address, 1000, "1MB.txt")
        recv = proto.recvDataPackets(address, sock)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send and recieve Reliable UDP locally')
    parser.add_argument('host')
    parser.add_argument('-p', metavar='PORT', type=int, default=6000, help='Reliable UDP port')
    args = parser.parse_args()
    client((args.host, args.p))

#To Run client use
#python server.py localhost
#netem settings commands
#sudo tc qdisc add dev lo root netem loss 90%