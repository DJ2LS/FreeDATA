#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 20:06:55 2020

@author: DJ2LS
"""

import logging
import socketserver
import freedv
import commands

class MyTCPHandler(socketserver.BaseRequestHandler):



    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print("{} wrote:".format(self.client_address[0]))
        print(self.data)
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())
        
        if self.data == b'TEST':
            logging.info("DER TEST KLAPPT! HIER KOMMT DER COMMAND PARSER HIN!")

# BROADCAST PARSER ###########################################################
        #if self.data == b'BC':
        if self.data.startswith(b'BC:'):
            data = self.data.split(b'BC:')
            commands.TX.Broadcast(bytes(data[1]),bytes(data[1]))
            #commands.TX.Broadcast(data,data)