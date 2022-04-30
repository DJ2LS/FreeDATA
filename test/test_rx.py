#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

import ctypes
from ctypes import *
import pathlib
import sounddevice as sd
import sys
import logging
import time
import threading
import sys
import argparse
import numpy as np
sys.path.insert(0,'..')
from tnc import codec2


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
    
    devices = sd.query_devices(device=None, kind=None)
    index = 0
    for device in devices:
        print(f"{index} {device['name']}")
        index += 1
    sd._terminate()
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
    # auto search for loopback devices
    if AUDIO_INPUT_DEVICE == -2:
        loopback_list = []
 
        devices = sd.query_devices(device=None, kind=None)
        index = 0
        
        for device in devices:
            if 'Loopback: PCM' in device['name']:
                print(index)
                loopback_list.append(index)
            index += 1
                
        if len(loopback_list) >= 1:
            AUDIO_INPUT_DEVICE = loopback_list[0] #0  = RX   1 = TX
            print(f"loopback_list tx: {loopback_list}", file=sys.stderr)
        else:
            print("not enough audio loopback devices ready...")
            print("you should wait about 30 seconds...")

            sd._terminate()
            quit()        
    print(f"AUDIO INPUT DEVICE: {AUDIO_INPUT_DEVICE}", file=sys.stderr)

    # audio stream init
    stream_rx = sd.RawStream(channels=1, dtype='int16', device=AUDIO_INPUT_DEVICE, samplerate = AUDIO_SAMPLE_RATE_RX, blocksize=4800)
    stream_rx.start()
             
# ----------------------------------------------------------------
              
# DATA CHANNEL INITIALISATION

# open codec2 instance        
freedv = cast(codec2.api.freedv_open(MODE), c_void_p)

# get number of bytes per frame for mode
bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(freedv)/8)
payload_bytes_per_frame = bytes_per_frame -2

n_max_modem_samples = codec2.api.freedv_get_n_max_modem_samples(freedv)     
bytes_out = create_string_buffer(bytes_per_frame)

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

# time meassurement
time_start = 0
time_end = 0

# Copy received 48 kHz to a file.  Listen to this file with:
#   aplay -r 48000 -f S16_LE rx48.raw
# Corruption of this file is a good way to detect audio card issues
frx = open("rx48.raw", mode='wb')    

# initial number of samples we need
nin = codec2.api.freedv_nin(freedv)
while receive and time.time() < timeout:
    if AUDIO_INPUT_DEVICE != -1:
        try:
            #data_in48k = stream_rx.read(AUDIO_FRAMES_PER_BUFFER, exception_on_overflow = True)
            data_in48k, overflowed = stream_rx.read(AUDIO_FRAMES_PER_BUFFER) 
        except OSError as err:
            print(err, file=sys.stderr)
            #if str(err).find("Input overflowed") != -1:
            #    nread_exceptions += 1
            #if str(err).find("Stream closed") != -1:
            #    print("Ending...")
            #    receive = False
    else:
        data_in48k = sys.stdin.buffer.read(AUDIO_FRAMES_PER_BUFFER*2)
    
    # insert samples in buffer
    x = np.frombuffer(data_in48k, dtype=np.int16)
    #print(x)
    #x = data_in48k
    x.tofile(frx)    
    if len(x) != AUDIO_FRAMES_PER_BUFFER:
        receive = False
    x = resampler.resample48_to_8(x)
    audio_buffer.push(x)
    
    # when we have enough samples call FreeDV Rx
    while audio_buffer.nbuffer >= nin:
        # start time measurement
        time_start = time.time()
        # demodulate audio
        nbytes = codec2.api.freedv_rawdatarx(freedv, bytes_out, audio_buffer.buffer.ctypes)        
        time_end = time.time()
        
        audio_buffer.pop(nin)
        
        # call me on every loop!
        nin = codec2.api.freedv_nin(freedv)
       
        rx_status = codec2.api.freedv_get_rx_status(freedv)       
        if rx_status & codec2.api.FREEDV_RX_BIT_ERRORS:
            rx_errors = rx_errors + 1
        if DEBUGGING_MODE:        
          rx_status = codec2.api.rx_sync_flags_to_text[rx_status]
          time_needed = time_end - time_start

          print("nin: %5d rx_status: %4s naudio_buffer: %4d time: %4s" % \
                (nin,rx_status,audio_buffer.nbuffer, time_needed), file=sys.stderr)

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


# and at last check if we had an opened audio instance and close it
if AUDIO_INPUT_DEVICE != -1:
    sd._terminate()


