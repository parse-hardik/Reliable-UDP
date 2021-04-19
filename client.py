from Protocol import Protocol
import argparse

def client(address, window_size):
    proto = Protocol()
    sock = proto.create_socket()
    sock.bind(('localhost', 5000))
    recv = False
    while not recv:
        proto.connect(sock, address, window_size, "1MB.txt")
        recv = proto.recvDataPackets(address, sock)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send and recieve Reliable UDP locally')
    # parser.add_argument('-h' , default="localhost" , help="chose host")
    parser.add_argument('-w' , default=8 , help="chose window size")
    parser.add_argument('-p', metavar='PORT', type=int, default=6000, help='Reliable UDP port')
    args = parser.parse_args()
    client(('localhost', args.p), int(args.w))

#To Run client use
#python server.py 
#netem settings commands
#sudo tc qdisc add dev lo root netem loss 90%
