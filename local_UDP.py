import argparse
import socket
from datetime import datetime

MAX_BYTES = 65555


def server(port):
	# AF_INET-->IPv4, Dgram--> Works on UDP
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind(('127.0.0.1', port))
	print('Server listening at {}'.format(sock.getsockname()))
	while True:
		data, address = sock.recvfrom(MAX_BYTES)
		text = data.decode('ascii')
		print('The client at {} says {!r}'.format(address, text))
		text = 'Your data was {} bytes long'.format(len(text))
		data = text.encode('ascii')
		sock.sendto(data, address)


def client(port):
	# AF_INET-->IPv4, Dgram--> Works on UDP
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	text = 'Time at my end is {}'.format(datetime.now())
	data = text.encode('ascii')
	sock.sendto(data, ('127.0.0.1', port))
	print('The OS assigned me the address {}'.format(sock.getsockname()))
	while True:
		data, address = sock.recvfrom(MAX_BYTES)
		text = data.decode('ascii')
		text = text.split('<!>')
		ack = int(text[3])
		msg = str(ack) + '<!>' + str(ack+1)
		sock.sendto(msg.encode(), ('127.0.0.1', port))
		print('The server at {} replied {!r}'.format(address, text))


if __name__ == '__main__':
	choices = {'client': client, 'server': server}
	parser = argparse.ArgumentParser(description='Send and recieve UDP locally')
	parser.add_argument('role', choices=choices, help='which role to play')
	parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='UDP port (default 53)')
	args = parser.parse_args()
	function = choices[args.role]
	function(args.p)
