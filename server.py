from Protocol import Protocol
import argparse

def server(address):
    proto = Protocol()
    sock = proto.create_socket()
    sock.bind(address)
    file_requested = proto.listen(sock)
    # with open(file_requested, "r") as file:
    info = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed quis fringilla leo. Morbi ultricies lorem at leo elementum, quis volutpat nulla pellentesque. Fusce vel turpis ac turpis finibus dapibus vitae vel enim. Vivamus eleifend ac risus sit amet gravida. Sed tempus at odio quis commodo. Praesent imperdiet ligula non sem egestas ultrices. Vestibulum posuere leo eget tristique ullamcorper. Nulla non tortor consectetur, viverra lorem sed, lobortis nisl.Nullam in pretium nisi. Morbi pulvinar quis mauris porta interdum. Vivamus eu magna id leo mollis luctus. Aliquam egestas nec lorem vel efficitur. Sed et quam eu erat fringilla consectetur et id tortor. Ut placerat lorem et finibus pellentesque. Vestibulum a fermentum libero, quis ornare ligula. Suspendisse tempus nec arcu vel eleifend. Vestibulum viverra mi eros, eget lacinia risus elementum nec. Maecenas sed suscipit velit. Integer id justo fermentum orci imperdiet lobortis. Quisque vitae velit ut ligula aliquam commodo. Ut viverra maximus vulputate. Praesent volutpat dolor ligula, commodo tincidunt eros vehicula et.Nulla auctor non lacus eget rutrum. Ut id nibh elit. Mauris sed quam nisi. Duis in vestibulum dui. Ut vitae tincidunt enim, blandit gravida dolor. Praesent rhoncus, nisl ut rhoncus tempor, sapien est feugiat eros, non dapibus purus felis in mauris. Curabitur tempus mauris quis leo vestibulum, vel iaculis diam facilisis. Aliquam mattis odio ac dolor venenatis vulputate. Aenean ac eros sollicitudin, mattis nunc at, gravida urna. Donec consequat turpis quis tristique finibus. Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae; Morbi sit amet ultricies orci. Aenean non posuere orci. Pellentesque nec nulla nec nunc congue consequat. Curabitur aliquam ipsum nec neque commodo, ut bibendum nunc ullamcorper.Vestibulum luctus, dui ac condimentum faucibus, nibh felis volutpat ante, vitae tincidunt lorem enim at sem. Maecenas egestas ac magna ut auctor. Duis nec pulvinar justo, vel laoreet dui. Nulla facilisi. Ut porta ipsum at magna faucibus, vitae congue ante laoreet. Praesent pellentesque efficitur sem sed volutpat. Suspendisse metus elit, dictum id mi vel, ultricies bibendum urna. Nam pulvinar dictum nunc sed sagittis. Vestibulum at molestie sapien. Morbi eros libero, consequat vel felis sed, convallis venenatis lectus. Mauris purus velit, sagittis a mi eget, lacinia euismod lectus. Phasellus molestie eleifend arcu, ut convallis ex ultrices id. Integer ultricies tempor arcu ac vulputate.Curabitur elit dui, cursus eget odio ac, rhoncus hendrerit nunc. Integer tortor nulla, tempus ac mi vitae, malesuada pulvinar sem. Fusce sit amet tincidunt arcu, nec fringilla nisi. Phasellus ut erat eu nulla vulputate aliquet sed at eros. Vestibulum ut pulvinar leo, in lobortis est. Curabitur convallis vel nunc vel ornare. Aliquam non lacinia tellus. Praesent nec risus euismod erat vehicula sagittis. Aenean sed massa varius, lobortis arcu in, commodo augue.@"
    proto.sendDataPackets(info, sock, address)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send and recieve Reliable UDP locally')
    parser.add_argument('host')
    parser.add_argument('-p', metavar='PORT', type=int, default=6000, help='Reliable UDP port')
    args = parser.parse_args()
    server((args.host, args.p))
