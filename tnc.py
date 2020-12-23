#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import socketserver
import threading

import modem
import static

modem = modem.RF()


class TCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        
     
        # interrupt listening loop "while true" by setting MODEM_RECEIVE to False
        if len(self.data) > 0:
            static.MODEM_RECEIVE = False
        
        
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())
        
        #if self.data == b'TEST':
            #logging.info("DER TEST KLAPPT! HIER KOMMT DER COMMAND PARSER HIN!")

# BROADCAST PARSER  -----------------------------------------------------------

        if self.data.startswith(b'BC:'):
            static.MODEM_RECEIVE = False
            print(static.MODEM_RECEIVE)
            
            data = self.data.split(b'BC:')
            daten = modem.Transmit(data[1])
            
            static.MODEM_RECEIVE = True
            print(static.MODEM_RECEIVE)