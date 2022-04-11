#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 16:58:45 2020

@author: DJ2LS

main module for running the tnc


"""


import argparse
import threading
import static
import socketserver
import helpers
import data_handler
import structlog
import log_handler
import modem
import sys
import os
import signal
import time
import multiprocessing


# signal handler for closing aplication
def signal_handler(sig, frame):
    """
    a signal handler, which closes the network/socket when closing the application
    Args:
      sig: signal
      frame: 

    Returns: system exit

    """
    print('Closing TNC...')
    sock.CLOSE_SIGNAL = True
    sys.exit(0)
    
signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    # we need to run this on windows for multiprocessing support
    multiprocessing.freeze_support()
    # --------------------------------------------GET PARAMETER INPUTS
    PARSER = argparse.ArgumentParser(description='FreeDATA TNC')
    PARSER.add_argument('--mycall', dest="mycall", default="AA0AA", help="My callsign", type=str)
    PARSER.add_argument('--ssid', dest="ssid_list", nargs='*', default=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], help="SSID list we are responding to", type=str)
    PARSER.add_argument('--mygrid', dest="mygrid", default="JN12AA", help="My gridsquare", type=str) 
    PARSER.add_argument('--rx', dest="audio_input_device", default=0, help="listening sound card", type=int)
    PARSER.add_argument('--tx', dest="audio_output_device", default=0, help="transmitting sound card", type=int)
    PARSER.add_argument('--port', dest="socket_port", default=3000, help="Socket port  in the range of 1024-65536", type=int)
    PARSER.add_argument('--deviceport', dest="hamlib_device_port", default="/dev/ttyUSB0", help="Hamlib device port", type=str)
    PARSER.add_argument('--devicename', dest="hamlib_device_name", default="2028", help="Hamlib device name", type=str)    
    PARSER.add_argument('--serialspeed', dest="hamlib_serialspeed", choices=[1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200], default=9600, help="Serialspeed", type=int)    
    PARSER.add_argument('--pttprotocol', dest="hamlib_ptt_type", choices=['USB', 'RIG', 'RTS', 'DTR', 'CM108', 'MICDATA', 'PARALLEL', 'DTR-H', 'DTR-L', 'NONE'], default='USB', help="PTT Type", type=str)    
    PARSER.add_argument('--pttport', dest="hamlib_ptt_port", default="/dev/ttyUSB0", help="PTT Port", type=str)        
    PARSER.add_argument('--data_bits', dest="hamlib_data_bits", choices=[7, 8], default=8, help="Hamlib data bits", type=int)         
    PARSER.add_argument('--stop_bits', dest="hamlib_stop_bits", choices=[1, 2], default=1, help="Hamlib stop bits", type=int)          
    PARSER.add_argument('--handshake', dest="hamlib_handshake", default="None", help="Hamlib handshake", type=str)          
    PARSER.add_argument('--radiocontrol', dest="hamlib_radiocontrol", choices=['disabled', 'direct', 'rigctl', 'rigctld'], default="disabled", help="Set how you want to control your radio")                 
    PARSER.add_argument('--rigctld_port', dest="rigctld_port", default=4532, type=int, help="Set rigctld port")    
    PARSER.add_argument('--rigctld_ip', dest="rigctld_ip", default="localhost", help="Set rigctld ip")    
    PARSER.add_argument('--scatter', dest="send_scatter", action="store_true", help="Send scatter information via network") 
    PARSER.add_argument('--fft', dest="send_fft", action="store_true", help="Send fft information via network") 
    PARSER.add_argument('--500hz', dest="low_bandwith_mode", action="store_true", help="Enable low bandwith mode ( 500 Hz only )") 
    PARSER.add_argument('--fsk', dest="enable_fsk", action="store_true", help="Enable FSK mode for ping, beacon and CQ") 
    PARSER.add_argument('--tuning_range_fmin', dest="tuning_range_fmin", choices=[-50.0, -100.0, -150.0, -200.0, -250.0], default=-50.0, help="Tuning range fmin", type=float)  
    PARSER.add_argument('--tuning_range_fmax', dest="tuning_range_fmax", choices=[50.0, 100.0, 150.0, 200.0, 250.0], default=50.0, help="Tuning range fmax", type=float)
    PARSER.add_argument('--tx-audio-level', dest="tx_audio_level", default=50, help="Set the tx audio level at an early stage", type=int)  
    
       
    ARGS = PARSER.parse_args()

    # additional step for beeing sure our callsign is correctly
    # in case we are not getting a station ssid
    # then we are forcing a station ssid = 0
    mycallsign = bytes(ARGS.mycall.upper(), 'utf-8')
    mycallsign = helpers.callsign_to_bytes(mycallsign)
    static.MYCALLSIGN = helpers.bytes_to_callsign(mycallsign)
    static.MYCALLSIGN_CRC = helpers.get_crc_16(static.MYCALLSIGN)  
    
    static.SSID_LIST = ARGS.ssid_list
      
    static.MYGRID = bytes(ARGS.mygrid, 'utf-8')
    static.AUDIO_INPUT_DEVICE = ARGS.audio_input_device
    static.AUDIO_OUTPUT_DEVICE = ARGS.audio_output_device
    static.PORT = ARGS.socket_port
    static.HAMLIB_DEVICE_NAME = ARGS.hamlib_device_name
    static.HAMLIB_DEVICE_PORT = ARGS.hamlib_device_port
    static.HAMLIB_PTT_TYPE = ARGS.hamlib_ptt_type
    static.HAMLIB_PTT_PORT = ARGS.hamlib_ptt_port
    static.HAMLIB_SERIAL_SPEED = str(ARGS.hamlib_serialspeed)
    static.HAMLIB_DATA_BITS = str(ARGS.hamlib_data_bits)
    static.HAMLIB_STOP_BITS = str(ARGS.hamlib_stop_bits)
    static.HAMLIB_HANDSHAKE = ARGS.hamlib_handshake
    static.HAMLIB_RADIOCONTROL = ARGS.hamlib_radiocontrol
    static.HAMLIB_RGICTLD_IP = ARGS.rigctld_ip
    static.HAMLIB_RGICTLD_PORT = str(ARGS.rigctld_port)
    static.ENABLE_SCATTER = ARGS.send_scatter
    static.ENABLE_FFT = ARGS.send_fft
    static.ENABLE_FSK = ARGS.enable_fsk    
    static.LOW_BANDWITH_MODE = ARGS.low_bandwith_mode    
    static.TUNING_RANGE_FMIN = ARGS.tuning_range_fmin    
    static.TUNING_RANGE_FMAX = ARGS.tuning_range_fmax                
    static.TX_AUDIO_LEVEL = ARGS.tx_audio_level     
        
        
    # we need to wait until we got all parameters from argparse first before we can load the other modules
    import sock     
    
    # config logging  
    try:  
        if sys.platform == 'linux':
            logging_path = os.getenv("HOME") + '/.config/' + 'FreeDATA/' + 'tnc'
            
        if sys.platform == 'darwin':
            logging_path = os.getenv("HOME") + '/Library/' + 'Application Support/' + 'FreeDATA/' + 'tnc' 
               
        if sys.platform == 'win32' or sys.platform == 'win64':
            logging_path = os.getenv('APPDATA') + '/' + 'FreeDATA/' + 'tnc'  
         
        if not os.path.exists(logging_path):
            os.makedirs(logging_path)
        log_handler.setup_logging(logging_path)
    except:
           structlog.get_logger("structlog").error("[DMN] logger init error")       

    
    
    structlog.get_logger("structlog").info("[TNC] Starting FreeDATA", author="DJ2LS", year="2022", version=static.VERSION)
    
    # start data handler
    data_handler.DATA()
    
    # start modem
    modem = modem.RF()


    # --------------------------------------------START CMD SERVER

    try:
        structlog.get_logger("structlog").info("[TNC] Starting TCP/IP socket", port=static.PORT)
        # https://stackoverflow.com/a/16641793
        socketserver.TCPServer.allow_reuse_address = True
        cmdserver = sock.ThreadedTCPServer((static.HOST, static.PORT), sock.ThreadedTCPRequestHandler)
        server_thread = threading.Thread(target=cmdserver.serve_forever)

        server_thread.daemon = True
        server_thread.start()

    except Exception as e:
        structlog.get_logger("structlog").error("[TNC] Starting TCP/IP socket failed", port=static.PORT, e=e)
        os._exit(1)
    while 1:
        time.sleep(1)
