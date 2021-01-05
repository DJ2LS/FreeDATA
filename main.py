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


import audio 


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


#test_thread = threading.Thread(target=audio.read_audio, name="Audio Listener")
#test_thread.start()
#test_thread2 = threading.Thread(target=modem.play_audio, name="Audio Listener2")
#test_thread2.start()


#--------------------------------------------START AUDIO THREAD  
#logging.info("STARTING AUDIO THREAD")
#static.MODEM_RECEIVE = True    
#audio_receiver_thread = threading.Thread(target=modem.Receive, name="Audio Listener")
#audio_receiver_thread.start()

#--------------------------------------------START AUDIO THREAD  

#static.MODEM_RECEIVE = True   

logging.info("STARTING 700D RX THREAD")
FREEDV_700D_THREAD = threading.Thread(target=modem.Receive, args=[7], name="700D Listener")
FREEDV_700D_THREAD.start()

#logging.info("STARTING DATAC1 RX THREAD") 
#FREEDV_DATAC1_THREAD = threading.Thread(target=modem.Receive, args=[10], name="DATAC1 Listener")
#FREEDV_DATAC1_THREAD.start()

#logging.info("STARTING DATAC2 RX THREAD") 
#FREEDV_DATAC2_THREAD = threading.Thread(target=modem.Receive, args=[11], name="DATAC2 Listener")
#FREEDV_DATAC2_THREAD.start()

logging.info("STARTING DATAC3 RX THREAD") 
FREEDV_DATAC3_THREAD = threading.Thread(target=modem.Receive, args=[12], name="DATAC3 Listener")
FREEDV_DATAC3_THREAD.start()




#--------------------------------------------START SERVER  
logging.info("STARTING TCP/IP SOCKET ON PORT " + str(static.PORT))
try:
    socketserver.TCPServer.allow_reuse_address = True #https://stackoverflow.com/a/16641793
    server = socketserver.TCPServer((static.HOST, static.PORT), tnc.TCPRequestHandler)
    server.serve_forever()
finally:
    server.server_close()