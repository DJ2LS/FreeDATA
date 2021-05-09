#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:58:45 2020

@author: DJ2LS

"""


import argparse
import threading


if __name__ == '__main__':


    # --------------------------------------------GET PARAMETER INPUTS
    PARSER = argparse.ArgumentParser(description='Simons TEST TNC')
    PARSER.add_argument('--rx', dest="audio_input_device", default=0, help="listening sound card", type=int)
    PARSER.add_argument('--tx', dest="audio_output_device", default=0, help="transmitting sound card", type=int)
    PARSER.add_argument('--port', dest="socket_port", default=3000, help="Socket port", type=int)
    PARSER.add_argument('--deviceport', dest="hamlib_device_port", default="/dev/ttyUSB", help="Socket port", type=str)
    PARSER.add_argument('--deviceid', dest="hamlib_device_id", default=311, help="Socket port", type=int)    

    ARGS = PARSER.parse_args()
    
    # we need to wait until we got all parameters from argparse first 
    import static
    import sock     
    import helpers
    
    static.AUDIO_INPUT_DEVICE = ARGS.audio_input_device
    static.AUDIO_OUTPUT_DEVICE = ARGS.audio_output_device
    static.PORT = ARGS.socket_port
    static.HAMLIB_DEVICE_ID = ARGS.hamlib_device_id
    static.HAMLIB_DEVICE_PORT = ARGS.hamlib_device_port

    # config logging
    helpers.setup_logging()

    # --------------------------------------------START CMD SERVER

    CMD_SERVER_THREAD = threading.Thread(target=sock.start_cmd_socket, name="cmd server")
    CMD_SERVER_THREAD.start()
    
    WATCHDOG_SERVER_THREAD = threading.Thread(target=helpers.watchdog, name="watchdog")
    WATCHDOG_SERVER_THREAD.start()    
