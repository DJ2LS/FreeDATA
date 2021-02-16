#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 21:25:14 2020

@author: DJ2LS
"""

import socketserver
import threading
import logging
import time

import static
import arq


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        data = str(self.request.recv(1024), 'utf-8')
        #cur_thread = threading.current_thread()
        #response = bytes("{}: {}".format(cur_thread.name, data), 'ascii')
        #self.request.sendall(response)
        #print(threading.enumerate())

        if data == 'SOCKETTEST':
            response = bytes("WELL DONE! YOU ARE ABLE TO COMMUNICATE WITH THE TNC", 'utf-8')
            self.request.sendall(response)
            
        # TRANSMIT ARQ MESSAGE    
        if data.startswith('ARQ:'):
            logging.info("CMD | NEW ARQ DATA")
            
            data = data.split('ARQ:')
            data_out = bytes(data[1], 'utf-8')

            TRANSMIT_ARQ = threading.Thread(target=arq.transmit, args=[data_out], name="TRANSMIT_ARQ")
            TRANSMIT_ARQ.start()



class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    socketserver.TCPServer.allow_reuse_address = True
    pass


