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
parser.add_argument('--framesperburst', dest="N_FRAMES_PER_BURST", default=0, type=int)
parser.add_argument('--mode', dest="FREEDV_MODE", default=14, type=int)
parser.add_argument('--audioinput', dest="AUDIO_INPUT", default=0, type=int)  
parser.add_argument('--debug', dest="DEBUGGING_MODE", action="store_true")  

args = parser.parse_args()

N_BURSTS = args.N_BURSTS
N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
AUDIO_INPUT_DEVICE = args.AUDIO_INPUT
MODE = args.FREEDV_MODE
DEBUGGING_MODE = args.DEBUGGING_MODE


# AUDIO PARAMETERS
AUDIO_FRAMES_PER_BUFFER = 2048 
MODEM_SAMPLE_RATE = 8000
AUDIO_SAMPLE_RATE_TX = 48000

# check if we want to use an audio device then do an pyaudio init
if AUDIO_INPUT_DEVICE != 0: 
    p = pyaudio.PyAudio()
    stream_rx = p.open(format=pyaudio.paInt16, 
                            channels=1,
                            rate=AUDIO_SAMPLE_RATE_RX,
                            frames_per_buffer=AUDIO_FRAMES_PER_BUFFER,
                            input=True,
                            input_device_index=AUDIO_INPUT_DEVICE,
                            ) 

# LOAD FREEDV
libname = "libcodec2.so"
c_lib = ctypes.CDLL(libname)

# ctypes function init        

c_lib.freedv_open.argype = [c_int]
c_lib.freedv_open.restype = c_void_p

c_lib.freedv_get_bits_per_modem_frame.argtype = [c_void_p]
c_lib.freedv_get_bits_per_modem_frame.restype = c_int

c_lib.freedv_nin.argtype = [c_void_p]
c_lib.freedv_nin.restype = c_int

c_lib.freedv_rawdatarx.argtype = [c_void_p, c_char_p, c_char_p]
c_lib.freedv_rawdatarx.restype = c_int

c_lib.freedv_get_n_max_modem_samples.argtype = [c_void_p]
c_lib.freedv_get_n_max_modem_samples.restype = c_int

c_lib.freedv_set_frames_per_burst.argtype = [c_void_p, c_int]
c_lib.freedv_set_frames_per_burst.restype = c_void_p
      
c_lib.freedv_get_rx_status.argtype = [c_void_p]
c_lib.freedv_get_rx_status.restype = c_int      

      
# ----------------------------------------------------------------
              

     # DATA CHANNEL INITIALISATION

# open codec2 instance        
freedv = cast(c_lib.freedv_open(MODE), c_void_p)

# get number of bytes per frame for mode
bytes_per_frame = int(c_lib.freedv_get_bits_per_modem_frame(freedv)/8)
payload_bytes_per_frame = bytes_per_frame -2

n_max_modem_samples = c_lib.freedv_get_n_max_modem_samples(freedv)     
bytes_out = create_string_buffer(bytes_per_frame * 2)

c_lib.freedv_set_frames_per_burst(freedv,N_FRAMES_PER_BURST)

        
total_n_bytes = 0
rx_total_frames = 0
rx_frames = 0
rx_bursts = 0
timeout = time.time() + 10
receive = True

while receive and time.time() < timeout:

    data_in = b''
    if AUDIO_INPUT_DEVICE != 0: 
        
        nin = c_lib.freedv_nin(freedv)
        nin_converted = int(nin*(AUDIO_SAMPLE_RATE_RX/MODEM_SAMPLE_RATE))
        if DEBUGGING_MODE == True:
            print(f"NIN:  {nin} [{nin_converted}]", file=sys.stderr)
        
        data_in = stream_rx.read(nin_converted,  exception_on_overflow = False)  
        data_in = audioop.ratecv(data_in,2,1,AUDIO_SAMPLE_RATE_RX, MODEM_SAMPLE_RATE, None) 
        data_in = data_in[0].rstrip(b'\x00') 

    else:
        nin = c_lib.freedv_nin(freedv) * 2
        data_in = sys.stdin.buffer.read(nin)

    nbytes = c_lib.freedv_rawdatarx(freedv, bytes_out, data_in) # demodulate audio
    total_n_bytes = total_n_bytes + nbytes
    
    if DEBUGGING_MODE == True:
        print(f"SYNC: {c_lib.freedv_get_rx_status(freedv)}", file=sys.stderr)
        
    if nbytes == bytes_per_frame:
        rx_total_frames = rx_total_frames + 1
        rx_frames = rx_frames + 1

        if rx_frames == N_FRAMES_PER_BURST:
            rx_frames = 0
            rx_bursts = rx_bursts + 1
            
        
    if rx_bursts == N_BURSTS:
        receive = False   
                   

print(f"RECEIVED BURSTS: {rx_bursts} RECEIVED FRAMES: {rx_total_frames}", file=sys.stderr)

# and at last check if we had an openend pyaudio instance and close it
if AUDIO_INPUT_DEVICE != 0: 
    stream_tx.close()
    p.terminate()
