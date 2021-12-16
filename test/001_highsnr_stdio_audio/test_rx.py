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
import sys
import logging
import time
import threading
import sys
import argparse
import numpy as np
sys.path.insert(0,'..')
import codec2

#--------------------------------------------GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--bursts', dest="N_BURSTS", default=1, type=int)
parser.add_argument('--framesperburst', dest="N_FRAMES_PER_BURST", default=1, type=int)
parser.add_argument('--mode', dest="FREEDV_MODE", type=str, choices=['datac0', 'datac1', 'datac3'])
parser.add_argument('--audiodev', dest="AUDIO_INPUT_DEVICE", default=-1, type=int,
                    help="audio device number to use, use -2 to automatically select a loopback device")  
parser.add_argument('--debug', dest="DEBUGGING_MODE", action="store_true")  
parser.add_argument('--timeout', dest="TIMEOUT", default=10, type=int, help="Timeout (seconds) before test ends")  
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
TIMEOUT = args.TIMEOUT

# AUDIO PARAMETERS
AUDIO_FRAMES_PER_BUFFER = 2400*2  # <- consider increasing if you get nread_exceptions > 0
MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
AUDIO_SAMPLE_RATE_RX = 48000

# make sure our resampler will work
assert (AUDIO_SAMPLE_RATE_RX / MODEM_SAMPLE_RATE) == codec2.api.FDMDV_OS_48

# check if we want to use an audio device then do an pyaudio init
if AUDIO_INPUT_DEVICE != -1: 
    p = pyaudio.PyAudio()
    # auto search for loopback devices
    if AUDIO_INPUT_DEVICE == -2:
        loopback_list = []
        for dev in range(0,p.get_device_count()):
            if 'Loopback: PCM' in p.get_device_info_by_index(dev)["name"]:
                loopback_list.append(dev)
        if len(loopback_list) >= 2:
            AUDIO_INPUT_DEVICE = loopback_list[0] #0  = RX   1 = TX
            print(f"loopback_list rx: {loopback_list}", file=sys.stderr)
        else:
            quit()
            
    print(f"AUDIO INPUT DEVICE: {AUDIO_INPUT_DEVICE} DEVICE: {p.get_device_info_by_index(AUDIO_INPUT_DEVICE)['name']}  \
            AUDIO SAMPLE RATE: {AUDIO_SAMPLE_RATE_RX}", file=sys.stderr)
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
nread_exceptions = 0
timeout = time.time() + TIMEOUT
receive = True
audio_buffer = codec2.audio_buffer(AUDIO_FRAMES_PER_BUFFER*2)
resampler = codec2.resampler()

# Copy received 48 kHz to a file.  Listen to this file with:
#   aplay -r 48000 -f S16_LE rx48.raw
# Corruption of this file is a good way to detect audio card issues
frx = open("rx48.raw", mode='wb')    

# initial number of samples we need
nin = codec2.api.freedv_nin(freedv)
while receive and time.time() < timeout:
    if AUDIO_INPUT_DEVICE != -1:
        try:
            data_in48k = stream_rx.read(AUDIO_FRAMES_PER_BUFFER, exception_on_overflow = True)
        except OSError as err:
            print(err, file=sys.stderr)
            if str(err).find("Input overflowed"):
                nread_exceptions += 1
            if str(err).find("Stream closed"):
                receive = False
    else:
        data_in48k = sys.stdin.buffer.read(AUDIO_FRAMES_PER_BUFFER*2)
    
    # insert samples in buffer
    x = np.frombuffer(data_in48k, dtype=np.int16)
    x.tofile(frx)    
    if len(x) != AUDIO_FRAMES_PER_BUFFER:
        receive = False
    x = resampler.resample48_to_8(x)
    audio_buffer.push(x)
    
    # when we have enough samples call FreeDV Rx
    while audio_buffer.nbuffer >= nin:

        # demodulate audio
        nbytes = codec2.api.freedv_rawdatarx(freedv, bytes_out, audio_buffer.buffer.ctypes)        
        audio_buffer.pop(nin)
        
        # call me on every loop!
        nin = codec2.api.freedv_nin(freedv)
       
        rx_status = codec2.api.freedv_get_rx_status(freedv)       
        if rx_status & codec2.api.FREEDV_RX_BIT_ERRORS:
            rx_errors = rx_errors + 1
        if DEBUGGING_MODE:        
          rx_status = codec2.api.rx_sync_flags_to_text[rx_status]
          print("nin: %5d rx_status: %4s naudio_buffer: %4d" % \
                (nin,rx_status,audio_buffer.nbuffer), file=sys.stderr)

        if nbytes:
            total_n_bytes = total_n_bytes + nbytes
            
            if nbytes == bytes_per_frame:
                rx_total_frames = rx_total_frames + 1
                rx_frames = rx_frames + 1

            if rx_frames == N_FRAMES_PER_BURST:
                rx_frames = 0
                rx_bursts = rx_bursts + 1
                          
            if rx_bursts == N_BURSTS:
                receive = False
                
    if time.time() >= timeout:
        print("TIMEOUT REACHED")
     
if nread_exceptions:
    print("nread_exceptions %d - receive audio lost! Consider increasing Pyaudio frames_per_buffer..." %  \
          nread_exceptions, file=sys.stderr)
print(f"RECEIVED BURSTS: {rx_bursts} RECEIVED FRAMES: {rx_total_frames} RX_ERRORS: {rx_errors}", file=sys.stderr)
frx.close()

# and at last check if we had an openend pyaudio instance and close it
if AUDIO_INPUT_DEVICE != -1: 
    stream_rx.close()
    p.terminate()
