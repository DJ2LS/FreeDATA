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
parser.add_argument('--mode', dest="FREEDV_MODE", default=0, type=int)
parser.add_argument('--input', dest="DATA_INPUT", type=str)  
parser.add_argument('--audioinput', dest="AUDIO_INPUT", default=0, type=int)  
parser.add_argument('--debug', dest="DEBUGGING_MODE", action="store_true")  

args = parser.parse_args()

N_BURSTS = args.N_BURSTS
N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
DATA_INPUT = args.DATA_INPUT
AUDIO_INPUT_DEVICE = args.AUDIO_INPUT
FREEDV_MODE = args.FREEDV_MODE
DEBUGGING_MODE = args.DEBUGGING_MODE

# 1024 good for mode 6
AUDIO_FRAMES_PER_BUFFER = 2048 
MODEM_SAMPLE_RATE = 8000








              
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
n_max_modem_samples = c_lib.freedv_get_n_max_modem_samples(freedv)     
bytes_out = (ctypes.c_ubyte * bytes_per_frame) #bytes_per_frame
bytes_out = bytes_out() #get pointer from bytes_out
        
total_n_bytes = 0
rx_total_frames = 0
rx_frames = 0
rx_bursts = 0
receive = True
while receive == True:
    time.sleep(0.01)

    data_in = b''
    if DATA_INPUT == "audio":
        
        nin = c_lib.freedv_nin(freedv)
        nin_converted = int(nin*(AUDIO_SAMPLE_RATE_RX/MODEM_SAMPLE_RATE))
        if DEBUGGING_MODE == True:
            print("-----------------------------")
            print("NIN:  " + str(nin) + " [ " + str(nin_converted) + " ]")
        
        data_in = stream_rx.read(nin_converted,  exception_on_overflow = False)  
        data_in = audioop.ratecv(data_in,2,1,AUDIO_SAMPLE_RATE_RX, MODEM_SAMPLE_RATE, None) 
        data_in = data_in[0].rstrip(b'\x00') 

    else:
        nin = c_lib.freedv_nin(freedv)*2
        data_in = sys.stdin.buffer.read(nin)

    c_lib.freedv_rawdatarx.argtype = [ctypes.POINTER(ctypes.c_ubyte), bytes_out, data_in] # check if really neccessary 
    nbytes = c_lib.freedv_rawdatarx(freedv, bytes_out, data_in) # demodulate audio
    total_n_bytes = total_n_bytes + nbytes
    if DEBUGGING_MODE == True:
        print("SYNC: " + str(c_lib.freedv_get_rx_status(freedv)))
        
    if nbytes == bytes_per_frame:
        rx_total_frames = rx_total_frames + 1
        rx_frames = rx_frames + 1

        if rx_frames == N_FRAMES_PER_BURST:
            rx_frames = 0
            rx_bursts = rx_bursts + 1
            c_lib.freedv_set_sync(freedv,0)
        
    if rx_bursts == N_BURSTS:
        receive = False   
                   
print("------------------------------")
print("BURSTS: " + str(rx_bursts))
print("TOTAL RECEIVED BYTES: " + str(total_n_bytes)) 
print("RECEIVED FRAMES: " + str(rx_total_frames)) 

