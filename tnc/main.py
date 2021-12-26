#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:58:45 2020

@author: DJ2LS

"""


import argparse
import threading
import static
import subprocess
import sys

import logging, structlog, log_handler






if __name__ == '__main__':

    # --------------------------------------------GET PARAMETER INPUTS
    PARSER = argparse.ArgumentParser(description='Simons TEST TNC')
    PARSER.add_argument('--rx', dest="audio_input_device", default=0, help="listening sound card", type=int)
    PARSER.add_argument('--tx', dest="audio_output_device", default=0, help="transmitting sound card", type=int)
    PARSER.add_argument('--port', dest="socket_port", default=3000, help="Socket port", type=int)
    PARSER.add_argument('--deviceport', dest="hamlib_device_port", default="/dev/ttyUSB0", help="Hamlib device port", type=str)
    PARSER.add_argument('--devicename', dest="hamlib_device_name", default=2028, help="Hamlib device name", type=str)    
    PARSER.add_argument('--serialspeed', dest="hamlib_serialspeed", default=9600, help="Serialspeed", type=str)    
    PARSER.add_argument('--pttprotocol', dest="hamlib_ptt_type", default='RTS', help="PTT Type", type=str)    
    PARSER.add_argument('--pttport', dest="hamlib_ptt_port", default="/dev/ttyUSB0", help="PTT Port", type=str)        
    
    ARGS = PARSER.parse_args()
    
    static.AUDIO_INPUT_DEVICE = ARGS.audio_input_device
    static.AUDIO_OUTPUT_DEVICE = ARGS.audio_output_device
    static.PORT = ARGS.socket_port
    static.HAMLIB_DEVICE_NAME = ARGS.hamlib_device_name
    static.HAMLIB_DEVICE_PORT = ARGS.hamlib_device_port
    static.HAMLIB_PTT_TYPE = ARGS.hamlib_ptt_type
    static.HAMLIB_PTT_PORT = ARGS.hamlib_ptt_port
    static.HAMLIB_SERIAL_SPEED = ARGS.hamlib_serialspeed
    
    # we need to wait until we got all parameters from argparse first before we can load the other modules
    import sock     
    import helpers
    
    

    # config logging
    #helpers.setup_logging()
    log_handler.setup_logging("tnc")

    # --------------------------------------------START CMD SERVER

    CMD_SERVER_THREAD = threading.Thread(target=sock.start_cmd_socket, name="cmd server")
    CMD_SERVER_THREAD.start()

