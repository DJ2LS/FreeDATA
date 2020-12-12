#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 16:54:35 2020

@author: DJ2LS
"""

import sys
import logging
import argparse
import socketserver

import freedv
import sound
import tnc
import commands






def main():
    
    parser = argparse.ArgumentParser(description='Simons TEST TNC')
    parser.add_argument('--rx-sound-device', dest="audio_input_device", default=False, help="The sound card used to rx.", type=int)
    parser.add_argument('--tx-sound-device', dest="audio_output_device", default=False, help="The sound card used to tx.", type=int)
    parser.add_argument('--list-sound-device', dest="list_sound_devices", action='store_true', help="List audio devices")
    parser.add_argument('--port', dest="socket_port", default=9000, help="Set the port, the socket is listening on.", type=int)  
    
    args = parser.parse_args()

    if args.list_sound_devices:
        for line in commands.Helpers.getAudioDevices():
            print(line)
        sys.exit(0)
    
    
    logger = logging.getLogger()
    logger.setLevel("INFO") #DEBUG>INFO>WARNING>ERROR>CRITICAL
    logger.info("SIMONS ERSTES TNC PROGRAMM....DURCHHALTEN!")

#LADE FreeDV Klasse sonst Fehler    
    try:
        modem = freedv.FreeDV()
    except OSError:
        logger.error("FREEDV NICHT GEFUNDEN")
        sys.exit(0)
    
#LADE Audio Klasse sonst Fehler    
    try:
        audio = sound.Audio(
                    defaultFrames = 1024 * 8,
                    audio_input_device=args.audio_input_device,
                    audio_output_device=args.audio_output_device,    
                    tx_sample_state = None,
                    audio_sample_rate=48000,
                    modem_sample_rate=8000,
                    frames_per_buffer=1024,
                    audio_channels=1, 
            )
        audio.Record()
        
    except OSError:
        logger.error("AUDIO NICHT GEFUNDEN")
        sys.exit(0)
        
#LADE TNC Klasse sonst Fehler    
    try:
        HOST, PORT = "localhost", args.socket_port
        try:
            logger.info("Starting SOCKET SERVER")
            server = socketserver.TCPServer((HOST, PORT), tnc.MyTCPHandler)
            server.serve_forever()
        finally:
            server.server_close()

    except OSError:
        logger.error("TNC NICHT GEFUNDEN")
        sys.exit(0)        
    
    ####################### TEST BEREICH ############################
    

  

    
    #################################################################
    
if __name__ == "__main__":
    main()