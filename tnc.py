#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 21:25:14 2020

@author: DJ2LS
"""

import socketserver
import threading
import logging


import static
import arq



class TCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        
     
        # interrupt listening loop "while true" by setting MODEM_RECEIVE to False
        #if len(self.data) > 0:
       #     static.MODEM_RECEIVE = False
        
        
        ####print("{} wrote:".format(self.client_address[0]))
        ####print(self.data)
        
        # just send back the same data, but upper-cased
        #####self.request.sendall(self.data.upper())
        
        #if self.data == b'TEST':
            #logging.info("DER TEST KLAPPT! HIER KOMMT DER COMMAND PARSER HIN!")

# BROADCAST PARSER  -----------------------------------------------------------

        if self.data.startswith(b'BC:'):
            #import modem
            #modem = modem.RF()
            
            static.MODEM_RECEIVE = True ####### FALSE....
            
            data = self.data.split(b'BC:')
            #modem.Transmit(data[1])
            
            static.MODEM_RECEIVE = True
           
            
# SEND AN ARQ FRAME  -----------------------------------------------------------

        if self.data.startswith(b'ACK:'):
            static.MODEM_RECEIVE = True ############## FALSE

            data = self.data.split(b'ACK:')
            data_out = data[1]
                    
            arq.transmit(data_out)
                           
      