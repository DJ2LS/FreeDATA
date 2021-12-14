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
sys.path.insert(0,'..')
import codec2

#--------------------------------------------GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--bursts', dest="N_BURSTS", default=0, type=int)
parser.add_argument('--framesperburst', dest="N_FRAMES_PER_BURST", default=0, type=int)
parser.add_argument('--mode', dest="FREEDV_MODE", type=str, choices=['datac0', 'datac1', 'datac3'])
parser.add_argument('--audiodev', dest="AUDIO_INPUT_DEVICE", default=-1, type=int, help="audio device number to use")  
parser.add_argument('--debug', dest="DEBUGGING_MODE", action="store_true")  
parser.add_argument('--list', dest="LIST", action="store_true", help="list audio devices by number and exit")  

args = parser.parse_args()

if args.LIST:
    p = pyaudio.PyAudio()
    for dev in range(0,p.get_device_count()):
        print("audiodev: ", dev, p.get_device_info_by_index(dev)["name"])
    quit()
   
N_BURSTS = args.N_BURSTS
N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
AUDIO_INPUT_DEVICE = args.AUDIO_INPUT_DEVICE
MODE = codec2.FREEDV_MODE[args.FREEDV_MODE].value
DEBUGGING_MODE = args.DEBUGGING_MODE


# AUDIO PARAMETERS
AUDIO_FRAMES_PER_BUFFER = 2048 
MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
AUDIO_SAMPLE_RATE_RX = 48000
assert (AUDIO_SAMPLE_RATE_RX % MODEM_SAMPLE_RATE) == 0

# check if we want to use an audio device then do an pyaudio init
if AUDIO_INPUT_DEVICE != -1: 
    p = pyaudio.PyAudio()
    stream_rx = p.open(format=pyaudio.paInt16, 
                            channels=1,
                            rate=AUDIO_SAMPLE_RATE_RX,
                            frames_per_buffer=AUDIO_FRAMES_PER_BUFFER,
                            input=True,
                            input_device_index=AUDIO_INPUT_DEVICE
                            ) 

      
# ----------------------------------------------------------------
              
# DATA CHANNEL INITIALISATION

# open codec2 instance        
freedv = cast(codec2.api.freedv_open(MODE), c_void_p)

# get number of bytes per frame for mode
bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(freedv)/8)
payload_bytes_per_frame = bytes_per_frame -2

n_max_modem_samples = codec2.api.freedv_get_n_max_modem_samples(freedv)     
bytes_out = create_string_buffer(bytes_per_frame * 2)

codec2.api.freedv_set_frames_per_burst(freedv,N_FRAMES_PER_BURST)

total_n_bytes = 0
rx_total_frames = 0
rx_frames = 0
rx_bursts = 0
rx_errors = 0
timeout = time.time() + 10
receive = True

while receive and time.time() < timeout:

    data_in = b''
    if AUDIO_INPUT_DEVICE != -1: 
        
        nin = codec2.api.freedv_nin(freedv)
        nin_converted = int(nin*(AUDIO_SAMPLE_RATE_RX/MODEM_SAMPLE_RATE))
        if DEBUGGING_MODE == True:
            print("nin: %5d nin_converted: %5d " % (nin,nin_converted), end='', file=sys.stderr)
        
        data_in = stream_rx.read(nin_converted,  exception_on_overflow = False)  
        data_in = audioop.ratecv(data_in,2,1,AUDIO_SAMPLE_RATE_RX, MODEM_SAMPLE_RATE, None) 
        data_in = data_in[0].rstrip(b'\x00') 

    else:
        nin = codec2.api.freedv_nin(freedv) * 2
        if DEBUGGING_MODE == True:
            print("nin: %5d " % (nin), end='', file=sys.stderr)
        data_in = sys.stdin.buffer.read(nin)

    nbytes = codec2.api.freedv_rawdatarx(freedv, bytes_out, data_in) # demodulate audio
    total_n_bytes = total_n_bytes + nbytes
    
    rx_status = codec2.api.freedv_get_rx_status(freedv)
    if DEBUGGING_MODE == True:
        rx_status_string = codec2.api.rx_sync_flags_to_text[rx_status]
        print(f"rx_status: {rx_status_string}", file=sys.stderr)
        
    if nbytes == bytes_per_frame:
        rx_total_frames = rx_total_frames + 1
        rx_frames = rx_frames + 1

        if rx_frames == N_FRAMES_PER_BURST:
            rx_frames = 0
            rx_bursts = rx_bursts + 1
            
    if rx_status & codec2.api.FREEDV_RX_BIT_ERRORS:
        rx_errors = rx_errors + 1
        
    if rx_bursts == N_BURSTS:
        receive = False   
                   

print(f"RECEIVED BURSTS: {rx_bursts} RECEIVED FRAMES: {rx_total_frames} RX_ERRORS: {rx_errors}", file=sys.stderr)

# and at last check if we had an openend pyaudio instance and close it
if AUDIO_INPUT_DEVICE != -1: 
    stream_rx.close()
    p.terminate()
