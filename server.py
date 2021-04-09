from Protocol import Protocol
import argparse

def server(address):
    proto = Protocol()
    sock = proto.create_socket()
    sock.bind(address)
    file_requested, add = proto.listen(sock)
    # info = "Enjoyed minutes related as at on on. Is fanny dried as often me. Goodness as reserved raptures to mistaken steepest oh screened he. Gravity he mr sixteen esteems. Mile home its new way with high told said."
    proto.sendFile(sock, add, file_requested)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send and recieve Reliable UDP locally')
    parser.add_argument('host')
    parser.add_argument('-p', metavar='PORT', type=int, default=6000, help='Reliable UDP port')
    args = parser.parse_args()
    server((args.host, args.p))

#To Run client use
#python client.py localhost