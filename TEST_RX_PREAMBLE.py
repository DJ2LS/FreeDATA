#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

import ctypes
from ctypes import *
import pathlib
import pyaudio
import audioop
import sys
import logging
import time
import threading
import helpers



WAITING_FOR_SIGNALLING = False

AUDIO_INPUT_DEVICE = 1
AUDIO_BUFFER_SIZE = 512
AUDIO_SAMPLE_RATE_RX = 44100

# 1024 good for mode 6
AUDIO_FRAMES_PER_BUFFER = 2048 
MODEM_SAMPLE_RATE = 8000

FREEDV_SIGNALLING_MODE = 7
FREEDV_MODE = 12

AUDIO_BUFFER = bytearray()

              
        #-------------------------------------------- LOAD FREEDV
             
libname = pathlib.Path().absolute() / "codec2/build_linux/src/libcodec2.so"
c_lib = ctypes.CDLL(libname)

        #--------------------------------------------CREATE PYAUDIO  INSTANCE
        
p = pyaudio.PyAudio()
        
        #--------------------------------------------GET SUPPORTED SAMPLE RATES FROM SOUND DEVICE
        
AUDIO_SAMPLE_RATE_RX = int(p.get_device_info_by_index(AUDIO_INPUT_DEVICE)['defaultSampleRate'])
        
        #--------------------------------------------OPEN AUDIO CHANNEL RX
        
stream_rx = p.open(format=pyaudio.paInt16, 
                            channels=1,
                            rate=AUDIO_SAMPLE_RATE_RX,
                            frames_per_buffer=AUDIO_FRAMES_PER_BUFFER,
                            input=True,
                            input_device_index=AUDIO_INPUT_DEVICE,
                            ) 



         
#--------------------------------------------------------------------------------------------------------
 
#--------------------------------------------------------------------------------------------------------    
    # DEMODULATE DATA AND RETURN IT
def receive():
        print("RECEIVE....")
        
    # GENERAL PARAMETERS        
        c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
                
    # SIGNALLING CHANNEL INITIALISATION
        freedv_signalling = c_lib.freedv_open(FREEDV_SIGNALLING_MODE)
        bytes_per_frame_signalling = int(c_lib.freedv_get_bits_per_modem_frame(freedv_signalling)/8)        
        bytes_out_signalling = (ctypes.c_ubyte * bytes_per_frame_signalling)
        bytes_out_signalling = bytes_out_signalling() #get pointer from bytes_out
 
     # DATA CHANNEL INITIALISATION

        freedv = c_lib.freedv_open(FREEDV_MODE)
        bytes_per_frame = int(c_lib.freedv_get_bits_per_modem_frame(freedv)/8)        
        bytes_out = (ctypes.c_ubyte * bytes_per_frame)
        bytes_out = bytes_out() #get pointer from bytes_out
        
        while 1:
            time.sleep(0.05)
            
            # -------------------------------------------------------------------------- DECODING SIGNALLING FRAMES
            cycles = 0
            while WAITING_FOR_SIGNALLING == True:
                time.sleep(0.01)
                
                #print("WAITING FOR SIGNALLING")
                print("-----------------------------")
                nin_signalling = c_lib.freedv_nin(freedv_signalling)
                print("NIN:           " + str(nin_signalling))
                nin_signalling = int(nin_signalling*(AUDIO_SAMPLE_RATE_RX/MODEM_SAMPLE_RATE))
                print("NIN CONVERTED: " + str(nin_signalling))
                
                data_in_signalling = stream_rx.read(nin_signalling,  exception_on_overflow = False)  
                data_in_signalling = audioop.ratecv(data_in_signalling,2,1,AUDIO_SAMPLE_RATE_RX, MODEM_SAMPLE_RATE, None) 
                #data_in_signalling = data_in_signalling[0]
                data_in_signalling = data_in_signalling[0].rstrip(b'\x00')  
                #data_in_signalling = data_in_signalling.strip(b'\x00')
                        
                if len(data_in_signalling) != b'':
                    c_lib.freedv_rawdatarx.argtype = [ctypes.POINTER(ctypes.c_ubyte), bytes_out_signalling, data_in_signalling] # check if really neccessary 
                    nbytes_signalling = c_lib.freedv_rawdatarx(freedv_signalling, bytes_out_signalling, data_in_signalling) # demodulate audio
                    
                    rx_status = c_lib.freedv_get_rx_status(freedv_signalling)
                    if rx_status == 0:
                        print("SYNC STATE:    0 - NO SYNC")
                    if rx_status == 1:
                        print("SYNC STATE:    1 - TRIAL SYNC")                
                    if rx_status == 2:
                        print("SYNC STATE:    2 - SYNC")                
                    if rx_status >= 3:
                        print("SYNC STATE:    >= OTHER - " + str(rx_status))    
                    

                    if nbytes_signalling == bytes_per_frame_signalling and c_lib.freedv_get_rx_status(freedv_signalling) == 7: # make sure, we receive a full frame
                        print("MODE: " + str(FREEDV_SIGNALLING_MODE) + " DATA: " + str(bytes(bytes_out_signalling)))

              
            # -------------------------------------------------------------------------- DECODING DATA FRAMES
            cycles = 0
            while WAITING_FOR_SIGNALLING == False:
                #time.sleep(0.01)
                
                #print("WAITING FOR DATA")
                
                print("-----------------------------")
                nin = c_lib.freedv_nin(freedv)
                print("NIN:           " + str(nin))
                nin = int(nin*(AUDIO_SAMPLE_RATE_RX/MODEM_SAMPLE_RATE))
                print("NIN CONVERTED: " + str(nin))
                
                
                data_in = stream_rx.read(nin,  exception_on_overflow = False)  
                data_in = audioop.ratecv(data_in,2,1,AUDIO_SAMPLE_RATE_RX, MODEM_SAMPLE_RATE, None) 
                data_in = data_in[0].rstrip(b'\x00') 
                print("DATA IN:       " + str(len(data_in)))
                
                c_lib.freedv_rawdatarx.argtype = [ctypes.POINTER(ctypes.c_ubyte), bytes_out, data_in] # check if really neccessary 
                nbytes = c_lib.freedv_rawdatarx(freedv, bytes_out, data_in) # demodulate audio
                
                rx_status = c_lib.freedv_get_rx_status(freedv)
                if rx_status == 0:
                    print("SYNC STATE:    0 - NO SYNC")
                if rx_status == 1:
                    print("SYNC STATE:    1 - TRIAL SYNC")                
                if rx_status == 2:
                    print("SYNC STATE:    2 - SYNC")                
                if rx_status >= 3:
                    print("SYNC STATE:    >= OTHER - " + str(rx_status))                
                
                
                
                
                if nbytes == bytes_per_frame:# and c_lib.freedv_get_rx_status(freedv_signalling) == 6: # make sure, we receive a full frame
                    print("MODE: " + str(FREEDV_MODE) + " CYCLES: " + str(cycles) + " DATA: " + str(bytes(bytes_out)))            
                else:
                    cycles = cycles + 1
                                
             
             
        #--------------------------------------------START RECEIVE THREAD        
        
FREEDV_RECEIVE_THREAD = threading.Thread(target=receive, name="Audio Listener")
FREEDV_RECEIVE_THREAD.start()   

