import socket
import hashlib
import time 
import threading

'''
***Group Members***

Rupsa Dhar - 2018A7PS0376H
Rishabh Jain - 2018A7PS0275H
Pranavi Marripudi - 2018A7PS0507H
Adesh Kumar Pradhan - 2017B3A70960H
Mereddy Aishwwarya Reddi - 2018A7PS0276H
'''

BUFFER = 500000
delim = "<!>"
max_retrans = 300
timeout_handshake = 10
timeout_acks = 0.5
msglen = 1024

class RelProtocol():

    win_size_self = 100
    win_size_other = 100

    def __init__(self):
        print("Protocol Initiated")

    def instPktDict(self):

        pkt_dict = {
            'pkt_type' : None,
            'syn' : None,
            'ack' : None,
            'fin' : None,
            'seq_num' : None,
            'exp_seq_num' : None,
            'message' : None,
            'checksum' : None,
            'valid_pkt' : None,
            'addr' : None,
            'timed_out' : None
        }

        return pkt_dict

    def makeSocket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return sock

    def closeSocket(self,sock):
        sock.close()

    # sender = server
    # receiver = client

    def threeWayConnect_sender(self,sock,win_size_sender):
        self.win_size_self = win_size_sender
        dummy_addr = ('localhost', 6565)
        # receive SYN
        ret_dict = self.recvPacket(sock,TIMEOUT=None)
        if ret_dict['valid_pkt'] == False: # if not valid
            print("recieving SYN timedout")
            return 0, dummy_addr
        if ret_dict['syn'] == 0: #syn
            print("case 2")
            return 0, dummy_addr
        print("recieved SYN")
        client_addr = ret_dict['addr']
        self.win_size_other = ret_dict['syn']
        # time.sleep(15)
        # send SYN+ACK
        self.sendDataPacket(1,1,0,-1,"SYN+ACK",sock,client_addr)
        print("sent SYN+ACK")

        # receive ACK
        # sock.settimeout(TIMEOUT)
        ret_dict = self.recvPacket(sock,TIMEOUT=1) #this needs timer
            # sock.settimeout(None)
        if ret_dict['valid_pkt']==False:
            return 0, dummy_addr
        if ret_dict['ack'] != 1 or ret_dict['seq_num'] != -1: #ack value
            print("case 4")
            return 0, dummy_addr
        print("recieved ACK")
        filename = ret_dict['message']
        return filename, client_addr
        

    def threeWayConnect_receiver(self,sock,server_addr,win_size_recv,filename):
        self.win_size_self = win_size_recv
        # send SYN
        self.sendDataPacket(self.win_size_self,0,0,0,"SYN",sock,server_addr) #random syn and ack
        print("sent SYN")

        # receive SYN+ACK 
        ret_dict = self.recvPacket(sock,TIMEOUT=1)
        if ret_dict['valid_pkt']==False:
            return 0
        if ret_dict['syn'] !=1 or ret_dict['ack']!=1 or ret_dict['seq_num'] != -1:
            return 0
        self.win_size_other = win_size_recv
        if ret_dict['message'] == "SYN+ACK":
            print("recieved SYN+ACK")
        # time.sleep(15)
        # send ACK

        self.sendDataPacket(0,1,0,-1,filename,sock,server_addr)
        # self.sendAckPacket(1,0,sock,server_addr)
        print("sent ACK")
        return 1 # 1 if success # 0 if fail

    
    # def CloseConnection(self): #when fin is set
        # pass

    def sendDataPacket(self, syn, ack, fin, seq_num, message, sock, addr):
        checksum = hashlib.sha1(message.encode()).hexdigest()
        sendStr = str(syn) + str(delim) + str(ack) + str(delim) + str(fin)  + str(delim) + str(seq_num) + str(delim) + str(message) + str(delim) + str(checksum)
        sock.sendto(sendStr.encode(), addr)

    def sendAckPacket(self, ack, exp_seq_num, sock, addr):
        sendStr = str(ack) + str(delim) + str(exp_seq_num)
        sock.sendto(sendStr.encode(), addr)

    def recvPacket(self,sock,TIMEOUT=None):
        pkt_dict = self.instPktDict()
        pkt_dict['timed_out']=False
        # recvfrom
        sock.settimeout(TIMEOUT)
        try:
            recv_pkt, recv_addr = sock.recvfrom(BUFFER)
            sock.settimeout(None)
        except Exception:
            pkt_dict['valid_pkt']=False
            pkt_dict['timed_out']=True
            sock.settimeout(None)
            return pkt_dict
        
        # both ACK and Data has to be handled
        #recv_pkt = pickle.loads(recv_pkt)
        recv_pkt = recv_pkt.decode()
        params = recv_pkt.split(delim)
        num_of_params = len(params)
        valid_pkt=False

        if num_of_params==2:
            valid_pkt=True
            pkt_dict['pkt_type'] = "ACK"
            pkt_dict['ack'] = int(params[0])
            pkt_dict['exp_seq_num'] = int(params[1])
            
        if num_of_params==6:
            pkt_dict['pkt_type'] = "DATA"
            pkt_dict['syn'] = int(params[0])
            pkt_dict['ack'] = int(params[1])
            pkt_dict['fin'] = int(params[2])
            pkt_dict['seq_num'] = int(params[3])
            pkt_dict['message'] = params[4]
            pkt_dict['checksum'] = params[5]
            if pkt_dict['checksum'] == hashlib.sha1(pkt_dict['message'].encode()).hexdigest():
                #print("CheckSum matching")
                valid_pkt=True  
        pkt_dict['valid_pkt'] = valid_pkt
        pkt_dict['addr'] = recv_addr
        # verify checksum
        # return (pkt num, pkt type- data | ACK) to the caller (SRQrecv, SRQsend)
        return pkt_dict

    def offsetSeq(self, base, the_seq_num):
        div = 2*self.win_size_self
        value = base + (the_seq_num%div + div - base%div)%div
        return value

    def SRQrecv(self,sock,addr): #this is for client

        mssgs = [""]*100000
        exp_seq_num = 0 #left end of window
        div = 2*self.win_size_self

        #map_seq = [i%div for i in range(10000)]

        while True:

            ret_dict = self.recvPacket(sock, 5)

            if ret_dict['fin'] == 1:
                #print("Fin received")
                #return mssgs, False
                while True:
                    self.sendDataPacket(0,1,1,0,"",sock,addr)
                    print("sent fin+ ack")
                    ret_dict = self.recvPacket(sock,5)
                    if ret_dict['valid_pkt']==False:
                        print("time out at final ack")
                        break
                    if ret_dict['valid_pkt']==True and ret_dict['ack']==1 and ret_dict['seq_num']==-1:
                        print("received ack")
                        break
                return mssgs, False

            if ret_dict['timed_out'] == True:
                print('Timed Out while recieving Fin')
                return mssgs, True

            if ret_dict['valid_pkt'] == True and ret_dict['pkt_type'] == "DATA":
                
                recvd_seq = ret_dict['seq_num']
                offset_exp_seq = exp_seq_num%div
                mod_val = (recvd_seq-offset_exp_seq)%div
                pkt_ack = exp_seq_num+mod_val
                #pkt_ack = exp_seq_num + recvd_seq - (exp_seq_num)%div

                #not duplicate and can be out of order
                if 0 <= mod_val <= (int(div/2)-1):
                    mssgs[pkt_ack] = ret_dict['message']
                    print(f'Recieved packet no = {pkt_ack}')


                

                # if exp_seq_num <= pkt_ack <= (exp_seq_num+self.win_size_self-1):
                #     mssgs[pkt_ack] = ret_dict['message']
                #     print(f'Recieved packet no = {pkt_ack}')

                # if len(mssgs[ret_dict['seq_num']]) == 0: #handled duplicates
                #     mssgs[ret_dict['seq_num']] = ret_dict['message']
                
                while len(mssgs[exp_seq_num]) != 0:
                    exp_seq_num += 1 #cumulative and window shift

                # if not (0 <= mod_val <= (int(div/2)-1)):
                #     self.sendAckPacket(recvd_seq, exp_seq_num%div, sock, addr)
                #     print(f'Sent Ack no = {pkt_ack} || Expected Packet no = {exp_seq_num}')

                if pkt_ack < exp_seq_num+div:
                    self.sendAckPacket(recvd_seq, exp_seq_num%div, sock, addr)
                    print(f'Sent Ack no = {pkt_ack} || Expected Packet no = {exp_seq_num}')




        return mssgs, False
  

    def SRQsend(self,data,sock,addr): # this is for server
        
        data_len = len(data)
        max_seq_num = int((len(data)-1)/msglen)
        total_pkts = max_seq_num+1
        print(f'total pkts = {total_pkts}')
        curr_seq_num = 0
        base_win = 0
        mssgs = list()
        max_trans_reached = False
        timeout_reached = False
        max_exp_seq_num = 0
        div = 2*self.win_size_self

        # for i in range(total_pkts):
        #     mssgs.append(data[i*msglen:min(msglen+i*msglen,data_len)])

        trans_count = [0]*total_pkts
        ack_status = [False]*total_pkts

        #send_sock = self.makeSocket()
        #send_sock.bind(('localhost',4200))

        def sendingPackets():

            #nonlocal base_win
            nonlocal max_trans_reached

            curr_seq_num = base_win

            while curr_seq_num < min(base_win+self.win_size_self, total_pkts):
                if trans_count[curr_seq_num] > max_retrans:
                    print("Max Transmission Reached")
                    max_trans_reached = True
                    return

                if ack_status[curr_seq_num] == False: #retransmission
                    offset_seq_num = curr_seq_num%div
                    self.sendDataPacket(0,0,0,offset_seq_num,data[curr_seq_num*msglen:min(msglen+curr_seq_num*msglen,data_len)].decode(),sock,addr)
                    trans_count[curr_seq_num] += 1
                    print(f'packet no = {curr_seq_num} || trans count = {trans_count[curr_seq_num]}')
                

                curr_seq_num += 1
        
        def receivingAcks():
            
            nonlocal max_exp_seq_num
            nonlocal timeout_reached
            timeout_count = 0
            no_of_acks = 0
            req_no_of_acks = 0
            curr_seq_num = base_win
            last_exp = -1
            count_last_exp = 0

            base = base_win

            while curr_seq_num < min(base_win+self.win_size_self, total_pkts):
                if ack_status[curr_seq_num] == False:
                    req_no_of_acks+=1
                curr_seq_num += 1

            while True:
                ret_dict = self.recvPacket(sock,timeout_acks)

                if ret_dict['timed_out'] == True:
                    print('Timed Out')   
                    return
                
                if ret_dict['valid_pkt'] == True and ret_dict['pkt_type'] == 'ACK':
                    real_ack = self.offsetSeq(base, ret_dict['ack'])
                    #real_ack = ret_dict['ack'] + base - (base)%div
                    if base <= real_ack < base+self.win_size_self:
                        ack_status[real_ack] = True #ack done
                        no_of_acks += 1
                    real_exp_seq_num = self.offsetSeq(base, ret_dict['exp_seq_num'])
                    #real_exp_seq_num = ret_dict['exp_seq_num'] + base - (base)%div

                    if base <= real_exp_seq_num <= base+self.win_size_self:
                        max_exp_seq_num = max(max_exp_seq_num, real_exp_seq_num) #cumulative/window shift
                        # for ind in range(max(0, max_exp_seq_num-div), max_exp_seq_num):
                        #     ack_status[ind] = True
                        # if max_exp_seq_num == total_pkts:
                        #   return
                        
                        if real_exp_seq_num == last_exp:
                            count_last_exp += 1


                            if count_last_exp == 3:
                                print("triple dup ack!")
                                self.sendDataPacket(0,0,0,last_exp%div,data[last_exp*msglen:min(msglen+last_exp*msglen,data_len)].decode(),sock,addr)


                        else:
                            last_exp = real_exp_seq_num
                            count_last_exp = 1

                # if real_exp_seq_num == total_pkts:
                #     timeout_reached = True

                print(f'Ack for packet no = {real_ack} || Expected packet no = {real_exp_seq_num}')
                # if real_exp_seq_num == total_pkts:
                #     max_trans_reached = True
                #     return

                if no_of_acks == req_no_of_acks: #only for required num of times
                    return
                    


        

        while base_win < total_pkts:

            sending_thread = threading.Thread(target=sendingPackets)
            receiving_thread = threading.Thread(target=receivingAcks)
            # sending_thread = Process(target=sendingPackets)
            # receiving_thread = Process(target=receivingAcks)

            print('New Window')
            sending_thread.start()
            receiving_thread.start()

            sending_thread.join()
            receiving_thread.join()

            # sendingPackets()
            # receivingAcks()
            if max_trans_reached == True or timeout_reached == True:
                return

            base_win = max_exp_seq_num #shifting window
        # parting handshake
        self.sendDataPacket(0,0,1,0,"Close",sock,addr)
        #self.sendDataPacket(0,0,1,0,"Close",sock,addr)
        print("sent FIN")


        while True:
            ret_dict = self.recvPacket(sock,5)
            if ret_dict['valid_pkt']==False:
                break
            if ret_dict['valid_pkt']== True and ret_dict['fin']==1 and ret_dict['ack']==1:
                print("received FIN +ACK")
                self.sendDataPacket(0,1,0,-1,"",sock,addr)
                print("sent final ACK")
                break
      
        return
        
'''  
        1 2 3 4 acked 6 7 8                 1 2 3 4 5 6 _ 8
        server     sender                   client  receiver
        
ack 6, exp_seq= 8
ack - 7
    
exp = 8  
exp = 6
7  8                      7 8'''