#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:58:45 2020

@author: DJ2LS

"""

import socketserver
import threading
import argparse
import logging

import tnc
import static
import modem

modem = modem.RF()


#--------------------------------------------GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--rx', dest="audio_input_device", default=0, help="sound card for listening.", type=int)
parser.add_argument('--tx', dest="audio_output_device", default=0, help="sound card for transmitting.", type=int)
parser.add_argument('--port', dest="socket_port", default=3000, help="Set the port, the socket is listening on.", type=int)  

args = parser.parse_args()


static.AUDIO_INPUT_DEVICE = args.audio_input_device
static.AUDIO_OUTPUT_DEVICE = args.audio_output_device
static.PORT = args.socket_port


#-------------------------------------------- DEFINE LOGGER    
logger = logging.getLogger()
logger.setLevel("INFO") #DEBUG>INFO>WARNING>ERROR>CRITICAL



#--------------------------------------------START AUDIO THREAD  
logging.info("STARTING AUDIO THREAD")
static.MODEM_RECEIVE = True    
audio_receiver_thread = threading.Thread(target=modem.Receive, name="Audio Listener")
audio_receiver_thread.start()


#--------------------------------------------START SERVER  
logging.info("STARTING TCP/IP SOCKET ON PORT " + str(static.PORT))
try:
    server = socketserver.TCPServer((static.HOST, static.PORT), tnc.TCPRequestHandler)
    server.serve_forever()
finally:
    server.server_close()