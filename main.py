#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:58:45 2020

@author: DJ2LS

"""


import argparse
import threading
import static
import helpers

if __name__ == '__main__':

    # config logging
    helpers.setup_logging()

    # --------------------------------------------GET PARAMETER INPUTS
    PARSER = argparse.ArgumentParser(description='Simons TEST TNC')
    PARSER.add_argument('--rx', dest="audio_input_device", default=0, help="listening sound card", type=int)
    PARSER.add_argument('--tx', dest="audio_output_device", default=0, help="transmitting sound card", type=int)
    PARSER.add_argument('--port', dest="socket_port", default=3000, help="Socket port", type=int)
    # parser.add_argument('--mode', dest="freedv_data_mode", default=12, help="Set the mode.", type=int)

    ARGS = PARSER.parse_args()

    # static.FREEDV_DATA_MODE = args.freedv_data_mode
    static.AUDIO_INPUT_DEVICE = ARGS.audio_input_device
    static.AUDIO_OUTPUT_DEVICE = ARGS.audio_output_device
    static.PORT = ARGS.socket_port

    # --------------------------------------------START CMD SERVER
    import sock  # we need to wait until we got all parameters from argparse first

    CMD_SERVER_THREAD = threading.Thread(target=sock.start_cmd_socket, name="cmd server")
    CMD_SERVER_THREAD.start()
