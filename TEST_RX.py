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
import sys
import argparse

#--------------------------------------------GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--bursts', dest="N_BURSTS", default=0, type=int)
parser.add_argument('--frames', dest="N_FRAMES_PER_BURST", default=0, type=int)
parser.add_argument('--delay', dest="DELAY_BETWEEN_BURSTS", default=0, type=int)
parser.add_argument('--mode', dest="FREEDV_MODE", default=0, type=int)
parser.add_argument('--input', dest="DATA_INPUT", type=str)  

args = parser.parse_args()

N_BURSTS = args.N_BURSTS
N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
DELAY_BETWEEN_BURSTS = args.DELAY_BETWEEN_BURSTS/1000
DATA_INPUT = args.DATA_INPUT

AUDIO_INPUT_DEVICE = 0
AUDIO_SAMPLE_RATE_RX = 44100

# 1024 good for mode 6
AUDIO_FRAMES_PER_BUFFER = 2048 
MODEM_SAMPLE_RATE = 8000

FREEDV_MODE = args.FREEDV_MODE
data_out = b'HELLO WORLD!'





              
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


    # GENERAL PARAMETERS        
c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
                

     # DATA CHANNEL INITIALISATION

freedv = c_lib.freedv_open(FREEDV_MODE)
bytes_per_frame = int(c_lib.freedv_get_bits_per_modem_frame(freedv)/8)        
bytes_out = (ctypes.c_ubyte * bytes_per_frame)
bytes_out = bytes_out() #get pointer from bytes_out
        
total_n_bytes = 0
receive = True
while receive == True:
    time.sleep(0.01)

    data_in = b''
    if DATA_INPUT == "audio":
        print("-----------------------------")
        nin = c_lib.freedv_nin(freedv)
        print("NIN:           " + str(nin))
        nin = int(nin*(AUDIO_SAMPLE_RATE_RX/MODEM_SAMPLE_RATE))
        print("NIN CONVERTED: " + str(nin))
        data_in = stream_rx.read(nin,  exception_on_overflow = False)  
        data_in = audioop.ratecv(data_in,2,1,AUDIO_SAMPLE_RATE_RX, MODEM_SAMPLE_RATE, None) 
        data_in = data_in[0].rstrip(b'\x00') 

    else:
        nin = c_lib.freedv_nin(freedv)*2
        data_in = sys.stdin.buffer.read(nin)

    c_lib.freedv_rawdatarx.argtype = [ctypes.POINTER(ctypes.c_ubyte), bytes_out, data_in] # check if really neccessary 
    nbytes = c_lib.freedv_rawdatarx(freedv, bytes_out, data_in) # demodulate audio
    total_n_bytes = total_n_bytes + nbytes

    if len(data_in) == 0:
        print("end of data")
        receive = False                          
print("------------------------------")             
print("TOTAL RECEIVED BYTES: " + str(total_n_bytes)) 
print("RECEIVED FRAMES: " + str(total_n_bytes//bytes_per_frame)) 

            
        #--------------------------------------------START RECEIVE THREAD        
 
