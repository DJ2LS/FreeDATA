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
import data_handler
import helpers
import fec


class CMDTCPRequestHandler(socketserver.BaseRequestHandler):    

    def handle(self):
    
        encoding = 'utf-8'    
        #data = str(self.request.recv(1024), 'utf-8')
        
        data = bytes()
        while True: 
            chunk = self.request.recv(8192)#.strip() 
            data += chunk
            if chunk.endswith(b'\n'):
                break
        data = data[:-1] # remove b'\n'
        data = str(data, 'utf-8')        

        # SOCKETTEST ---------------------------------------------------
        if data == 'SOCKETTEST':
            cur_thread = threading.current_thread()
            response = bytes("WELL DONE! YOU ARE ABLE TO COMMUNICATE WITH THE TNC", encoding)
            self.request.sendall(response)
        
        # CQ CQ CQ -----------------------------------------------------
        if data == 'CQCQCQ':
            for i in range(0,3):
                data_handler.transmit_cq()
                while static.ARQ_STATE == 'SENDING_SIGNALLING':
                    time.sleep(0.1)
                    pass

        
        # PING ----------------------------------------------------------
        if data.startswith('PING:'):
            #send ping frame and wait for ACK
            pingcommand = data.split('PING:')
            dxcallsign = pingcommand[1]
            data_handler.transmit_ping(dxcallsign)
        
        
        # ARQ CONNECT TO CALLSIGN ----------------------------------------
        if data.startswith('ARQ:CONNECT:'):
            arqconnectcommand = data.split('ARQ:CONNECT:')
            dxcallsign = arqconnectcommand[1]
            if static.ARQ_STATE == 'CONNECTED':
                # here we should disconnect
                pass
   
            if static.TNC_STATE == 'IDLE':
                # here we send an "CONNECT FRAME
                
                ARQ_CONNECT_THREAD = threading.Thread(target=data_handler.arq_connect, args=[dxcallsign], name="ARQ_CONNECT")
                ARQ_CONNECT_THREAD.start()
        
        # ARQ DISCONNECT FROM CALLSIGN ----------------------------------------
        if data == 'ARQ:DISCONNECT':

            ARQ_DISCONNECT_THREAD = threading.Thread(target=data_handler.arq_disconnect, name="ARQ_DISCONNECT")
            ARQ_DISCONNECT_THREAD.start()  

      
        
            
        # TRANSMIT ARQ MESSAGE ------------------------------------------   
        # wen need to change the TNC_STATE to "CONNECTE" and need to make sure we have a valid callsign and callsign crc8 of the DX station
        if data.startswith('ARQ:DATA') and static.TNC_STATE == b'IDLE':
            logging.info("CMD | NEW ARQ DATA")
            static.TNC_STATE = 'BUSY'
            arqdata = data.split('ARQ:')
            data_out = bytes(arqdata[1], 'utf-8')

            TRANSMIT_ARQ = threading.Thread(target=data_handler.transmit, args=[data_out], name="TRANSMIT_ARQ")
            TRANSMIT_ARQ.start()
        
        
        
        # SETTINGS AND STATUS ---------------------------------------------   
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
        
        if data == 'GET:TNC_STATE':
            self.request.sendall(static.TNC_STATE)
            
        if data == 'GET:PTT_STATE':
            self.request.sendall(bytes(str(static.PTT_STATE), encoding))       
        
        
        
                
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
