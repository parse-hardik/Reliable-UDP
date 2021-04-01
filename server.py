from Protocol import Protocol
import argparse

def server(address):
    proto = Protocol()
    sock = proto.create_socket()
    sock.bind(address)
    ans = proto.listen(sock)
    print(ans)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send and recieve Reliable UDP locally')
    parser.add_argument('host')
    parser.add_argument('-p', metavar='PORT', type=int, default=6000, help='Reliable UDP port')
    args = parser.parse_args()
    server((args.host, args.p))
