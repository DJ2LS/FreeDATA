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
import helpers

class CMDTCPRequestHandler(socketserver.BaseRequestHandler):    

    def handle(self):
    
        encoding = 'utf-8'    
        data = str(self.request.recv(1024), 'utf-8')

        # SOCKETTEST
        if data == 'SOCKETTEST':
            cur_thread = threading.current_thread()
            response = bytes("WELL DONE! YOU ARE ABLE TO COMMUNICATE WITH THE TNC", encoding)
            self.request.sendall(response)
            
        # TRANSMIT ARQ MESSAGE    
        if data.startswith('ARQ:') and static.TNC_STATE == b'IDLE':
            logging.info("CMD | NEW ARQ DATA")
            static.TNC_STATE = b'BUSY'
            arqdata = data.split('ARQ:')
            data_out = bytes(arqdata[1], 'utf-8')

            TRANSMIT_ARQ = threading.Thread(target=arq.transmit, args=[data_out], name="TRANSMIT_ARQ")
            TRANSMIT_ARQ.start()
        
        
        
        # SETTINGS AND STATUS    
        if data.startswith('SET:MYCALLSIGN:'):
            data = data.split('SET:MYCALLSIGN:')
            if bytes(data[1], encoding) == b'':
                self.request.sendall(b'INVALID CALLSIGN')
            else:    
                static.MYCALLSIGN = bytes(data[1], encoding)
                static.MYCALLSIGN_CRC8 = helpers.get_crc_8(static.MYCALLSIGN)
                self.request.sendall(static.MYCALLSIGN)
                logging.info("CMD | MYCALLSIGN: " + str(static.MYCALLSIGN))
         
         
        if data == 'GET:MYCALLSIGN':
            self.request.sendall(bytes(static.MYCALLSIGN, encoding))
                        
        if data == 'GET:MYCALLSIGN_CRC8':
            self.request.sendall(bytes(static.MYCALLSIGN_CRC8, encoding))
            
        if data == 'GET:DXCALLSIGN':
            self.request.sendall(bytes(static.DXCALLSIGN, encoding))              
            
        # ARQ
        if data == 'GET:ARQ_STATE':
            self.request.sendall(bytes(static.ARQ_STATE, encoding))
            
        if data == 'GET:TX_N_MAX_RETRIES':
            self.request.sendall(bytes([static.TX_N_MAX_RETRIES], encoding))
            
        if data == 'GET:TX_N_RETRIES':
            self.request.sendall(bytes([static.TX_N_RETRIES], encoding))
            
        if data == 'GET:ARQ_TX_N_FRAMES_PER_BURST':
            self.request.sendall(bytes([static.ARQ_TX_N_FRAMES_PER_BURST], encoding))
            
        if data == 'GET:ARQ_TX_N_BURSTS':
            self.request.sendall(bytes([static.ARQ_TX_N_BURSTS], encoding))
            
        if data == 'GET:ARQ_TX_N_CURRENT_ARQ_FRAME':
            self.request.sendall(bytes([static.ARQ_TX_N_CURRENT_ARQ_FRAME], encoding))
            
        if data == 'GET:ARQ_TX_N_TOTAL_ARQ_FRAMES':
            self.request.sendall(bytes([static.ARQ_TX_N_TOTAL_ARQ_FRAMES], encoding))
            
        if data == 'GET:ARQ_RX_FRAME_N_BURSTS':
            self.request.sendall(bytes([static.ARQ_RX_FRAME_N_BURSTS], encoding))
            
        if data == 'GET:ARQ_RX_N_CURRENT_ARQ_FRAME':
            self.request.sendall(bytes([static.ARQ_RX_N_CURRENT_ARQ_FRAME], encoding))
                    
        if data == 'GET:ARQ_N_ARQ_FRAMES_PER_DATA_FRAME':
            self.request.sendall(bytes([static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME], encoding))
            
        if data == 'GET:RX_BUFFER_LENGTH':
            self.request.sendall(bytes(str(len(static.RX_BUFFER)),encoding))

        if data.startswith('GET:RX_BUFFER:'):
            
            data = data.split('GET:RX_BUFFER:')
            bufferposition = int(data[1])-1
            if bufferposition == -1:
                if len(static.RX_BUFFER) > 0:
                    self.request.sendall(static.RX_BUFFER[-1])
           
            if bufferposition <= len(static.RX_BUFFER) > 0:
                    self.request.sendall(bytes(static.RX_BUFFER[bufferposition]))
                 

        if data == 'DEL:RX_BUFFER':
            static.RX_BUFFER = []





def start_cmd_socket():

    try:
        logging.info("SRV | STARTING TCP/IP SOCKET FOR CMD ON PORT: " + str(static.PORT))
        socketserver.TCPServer.allow_reuse_address = True #https://stackoverflow.com/a/16641793
        cmdserver = socketserver.TCPServer((static.HOST, static.PORT), CMDTCPRequestHandler)
        cmdserver.serve_forever()
    
    finally:
        cmdserver.server_close()
