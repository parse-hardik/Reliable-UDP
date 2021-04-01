from Protocol import Protocol
import argparse

def client(address):
    proto = Protocol()
    sock = proto.create_socket()
    sock.bind(('localhost', 5000))
    conn = proto.connect(sock, address, 5, "trial2.txt")
    print(conn)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send and recieve Reliable UDP locally')
    parser.add_argument('host')
    parser.add_argument('-p', metavar='PORT', type=int, default=6000, help='Reliable UDP port')
    args = parser.parse_args()
    client((args.host, args.p))
