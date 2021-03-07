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


      

if __name__ == '__main__':

    # config logging
    helpers.setup_logging()


    #--------------------------------------------GET PARAMETER INPUTS  
    parser = argparse.ArgumentParser(description='Simons TEST TNC')
    parser.add_argument('--rx', dest="audio_input_device", default=0, help="sound card for listening.", type=int)
    parser.add_argument('--tx', dest="audio_output_device", default=0, help="sound card for transmitting.", type=int)
    parser.add_argument('--port', dest="socket_port", default=3000, help="Set the port, the socket is listening on.", type=int)  
    #parser.add_argument('--mode', dest="freedv_data_mode", default=12, help="Set the mode.", type=int)
   
    args = parser.parse_args()
    
    #static.FREEDV_DATA_MODE = args.freedv_data_mode
    static.AUDIO_INPUT_DEVICE = args.audio_input_device
    static.AUDIO_OUTPUT_DEVICE = args.audio_output_device
    static.PORT = args.socket_port
        
    #--------------------------------------------START CMD SERVER         
    import sock # we need to wait until we got all parameters from argparse first before loading sock

    cmd_server_thread = threading.Thread(target=sock.start_cmd_socket, name="cmd server")
    cmd_server_thread.start()



