#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import socketserver
import threading

import modem
import static
#from other import *
import other
modem = modem.RF()


class TCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        
     
        # interrupt listening loop "while true" by setting MODEM_RECEIVE to False
        #if len(self.data) > 0:
       #     static.MODEM_RECEIVE = False
        
        
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())
        
        #if self.data == b'TEST':
            #logging.info("DER TEST KLAPPT! HIER KOMMT DER COMMAND PARSER HIN!")

# BROADCAST PARSER  -----------------------------------------------------------

        if self.data.startswith(b'BC:'):
            static.MODEM_RECEIVE = True ####### FALSE....
            print(static.MODEM_RECEIVE)
            
            data = self.data.split(b'BC:')
            daten = modem.Transmit(data[1])
            
            static.MODEM_RECEIVE = True
            print(static.MODEM_RECEIVE)
            
            
            
# ACKNOWLEDGE PARSER  -----------------------------------------------------------

        if self.data.startswith(b'ACK:'):
            static.MODEM_RECEIVE = True ############## FALSE
            print(static.MODEM_RECEIVE)
            
            data = self.data.split(b'ACK:')
            data_out = data[1]
            
            
            TXbuffer = [data_out[i:i+24] for i in range(0, len(data_out), 24)] # split incomming bytes to size of 30bytes, create a list and loop through it  
            TXbuffer_length = len(TXbuffer)
            for i in range(TXbuffer_length): # LOOP THROUGH DATA LIST
                
                #--------------------------------------------- BUILD DATA PACKET
                ack = b'REQACK'
                data_to_transmit = ack + TXbuffer[i]
                
                
                print(len(data_to_transmit))
                print(data_to_transmit)
                #---------------------------------------------------------------    
        
            
                static.ACK_RETRY = 1
                for static.ACK_RETRY in range(static.TX_RETRIES):
                    print("RETRY: " + str(static.ACK_RETRY))
                    print("SENDING")
                    static.ACK_RECEIVED = 0
                    daten = modem.Transmit(data_to_transmit)
                    
                    # --------------------------- START TIMER
                    static.ACK_TIMEOUT = 0
                    timer = threading.Timer(10.0, other.timeout)
                    timer.start() 

                    # --------------------------- WHILE TIMEOUT NOT REACHED LISTEN
                    print("WAITING FOR ACK")
                    while static.ACK_TIMEOUT == 0 and static.ACK_RECEIVED == 0:
                        static.MODEM_RECEIVE = True   
                    
                    if static.ACK_RECEIVED == 1:
                        static.ACK_RETRY = 3
                        break
                    
                if static.ACK_RECEIVED ==1:
                    break
                    
                        
            print("GESCHAFFT!")    
                           
      