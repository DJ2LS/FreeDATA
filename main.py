#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:58:45 2020

@author: DJ2LS

"""

import socketserver
import argparse
import logging
import threading

import static
import helpers



def start_cmd_socket():

    try:
        logging.info("SRV | STARTING TCP/IP CMD ON PORT: " + str(static.PORT))
        socketserver.TCPServer.allow_reuse_address = True #https://stackoverflow.com/a/16641793
        cmdserver = socketserver.TCPServer((static.HOST, static.PORT), sock.CMDTCPRequestHandler)
        cmdserver.serve_forever()
    
    finally:
        cmdserver.server_close()
        
        
def start_data_socket():

    try:
        logging.info("SRV | STARTING TCP/IP DATA ON PORT: " + str(static.PORT + 1))
        socketserver.TCPServer.allow_reuse_address = True #https://stackoverflow.com/a/16641793
        dataserver = socketserver.TCPServer((static.HOST, static.PORT + 1), sock.DATATCPRequestHandler)
        dataserver.serve_forever()
    
    finally:
        dataserver.server_close()   


     





        
        
        
        

if __name__ == '__main__':

    # config logging
    helpers.setup_logging()
    
    # list audio devices
    helpers.list_audio_devices()
    
    

    static.MYCALLSIGN = b'DJ2LS'
    static.MYCALLSIGN_CRC8 = helpers.get_crc_8(static.MYCALLSIGN)

    static.DXCALLSIGN = b'DH3WO'
    static.DXCALLSIGN_CRC8 =  helpers.get_crc_8(static.DXCALLSIGN)

    print("MYCALLSIGN " + str(static.MYCALLSIGN))
    print("MYCALLSIGN_CRC8 " + str(static.MYCALLSIGN_CRC8))
    
    print("DXCALLSIGN " + str(static.DXCALLSIGN))
    print("DXCALLSIGN_CRC8 " + str(static.DXCALLSIGN_CRC8))



    #--------------------------------------------GET PARAMETER INPUTS  
    parser = argparse.ArgumentParser(description='Simons TEST TNC')
    parser.add_argument('--rx', dest="audio_input_device", default=0, help="sound card for listening.", type=int)
    parser.add_argument('--tx', dest="audio_output_device", default=0, help="sound card for transmitting.", type=int)
    parser.add_argument('--port', dest="socket_port", default=3000, help="Set the port, the socket is listening on.", type=int)  
    parser.add_argument('--mode', dest="freedv_data_mode", default=12, help="Set the mode.", type=int)
   
    args = parser.parse_args()
    
    
    
    static.FREEDV_DATA_MODE = args.freedv_data_mode
    static.AUDIO_INPUT_DEVICE = args.audio_input_device
    static.AUDIO_OUTPUT_DEVICE = args.audio_output_device
    static.PORT = args.socket_port
    
    import sock # we need to wait until we got all parameters from argparse

    
    
    
    
    #--------------------------------------------START CMD & DATA SERVER  
  
    cmd_server_thread = threading.Thread(target=start_cmd_socket, name="cmd server")
    cmd_server_thread.start()
  
    data_server_thread = threading.Thread(target=start_data_socket, name="data server")
    data_server_thread.start()
        
  

