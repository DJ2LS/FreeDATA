#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pyaudio
import audioop
import time
import argparse
import sys
import ctypes
from ctypes import *
import pathlib
sys.path.insert(0,'..')
import codec2

#--------------------------------------------GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--bursts', dest="N_BURSTS", default=0, type=int)
parser.add_argument('--framesperburst', dest="N_FRAMES_PER_BURST", default=0, type=int)
parser.add_argument('--audioinput', dest="AUDIO_INPUT", default=0, type=int)  
parser.add_argument('--debug', dest="DEBUGGING_MODE", action="store_true") 

args = parser.parse_args()

N_BURSTS = args.N_BURSTS
N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
AUDIO_INPUT_DEVICE = args.AUDIO_INPUT


# SET COUNTERS
rx_total_frames_datac0 = 0
rx_frames_datac0 = 0
rx_bursts_datac0 = 0

rx_total_frames_datac1 = 0
rx_frames_datac1 = 0
rx_bursts_datac1 = 0

rx_total_frames_datac3 = 0
rx_frames_datac3 = 0
rx_bursts_datac3 = 0


# open codec2 instance        
datac0_freedv = cast(codec2.api.freedv_open(14), c_void_p)
datac0_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(datac0_freedv)/8)
datac0_n_max_modem_samples = codec2.api.freedv_get_n_max_modem_samples(datac0_freedv)
datac0_bytes_out = create_string_buffer(datac0_bytes_per_frame * 2)
codec2.api.freedv_set_frames_per_burst(datac0_freedv,N_FRAMES_PER_BURST)
datac0_buffer = bytes()

datac1_freedv = cast(codec2.api.freedv_open(10), c_void_p)
datac1_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(datac1_freedv)/8)
datac1_n_max_modem_samples = codec2.api.freedv_get_n_max_modem_samples(datac1_freedv)
datac1_bytes_out = create_string_buffer(datac1_bytes_per_frame * 2)
codec2.api.freedv_set_frames_per_burst(datac1_freedv,N_FRAMES_PER_BURST)
datac1_buffer = bytes()

datac3_freedv = cast(codec2.api.freedv_open(12), c_void_p)
datac3_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(datac3_freedv)/8)
datac3_n_max_modem_samples = codec2.api.freedv_get_n_max_modem_samples(datac3_freedv)
datac3_bytes_out = create_string_buffer(datac3_bytes_per_frame * 2)
codec2.api.freedv_set_frames_per_burst(datac3_freedv,N_FRAMES_PER_BURST)
datac3_buffer = bytes()

# check if we want to use an audio device then do an pyaudio init
if AUDIO_INPUT_DEVICE != 0: 
    p = pyaudio.PyAudio()
    # --------------------------------------------OPEN AUDIO CHANNEL RX
    stream_rx = p.open(format=pyaudio.paInt16,
                                     channels=1,
                                     rate=48000,
                                     frames_per_buffer=16,
                                     input=True,
                                     input_device_index=5
                                     )
                                     

timeout = time.time() + 10
receive = True

while receive and time.time() < timeout:
    if AUDIO_INPUT_DEVICE != 0: 
        data_in = stream_rx.read(1024,  exception_on_overflow=True)
        data_in = audioop.ratecv(data_in, 2, 1, 48000, 8000, None)
        data_in = data_in[0]  # .rstrip(b'\x00')
    else:
        data_in = sys.stdin.buffer.read(1024)
        
                
    datac0_buffer += data_in
    datac1_buffer += data_in
    datac3_buffer += data_in
                
        
    datac0_nin = codec2.api.freedv_nin(datac0_freedv) * 2            
        
    if len(datac0_buffer) >= (datac0_nin):        
        datac0_audio = datac0_buffer[:datac0_nin]
        datac0_buffer = datac0_buffer[datac0_nin:]
        nbytes = codec2.api.freedv_rawdatarx(datac0_freedv, datac0_bytes_out, datac0_audio)  # demodulate audio
        if nbytes == datac0_bytes_per_frame:
            rx_total_frames_datac0 = rx_total_frames_datac0 + 1
            rx_frames_datac0 = rx_frames_datac0 + 1

            if rx_frames_datac0 == N_FRAMES_PER_BURST:
                rx_frames_datac0 = 0
                rx_bursts_datac0 = rx_bursts_datac0 + 1
               
       
    datac1_nin = codec2.api.freedv_nin(datac1_freedv) * 2            
    if len(datac1_buffer) >= (datac1_nin):        
        datac1_audio = datac1_buffer[:datac1_nin]
        datac1_buffer = datac1_buffer[datac1_nin:]
        nbytes = codec2.api.freedv_rawdatarx(datac1_freedv, datac1_bytes_out, datac1_audio)  # demodulate audio
        if nbytes == datac1_bytes_per_frame:
            rx_total_frames_datac1 = rx_total_frames_datac1 + 1
            rx_frames_datac1 = rx_frames_datac1 + 1

            if rx_frames_datac1 == N_FRAMES_PER_BURST:
                rx_frames_datac1 = 0
                rx_bursts_datac1 = rx_bursts_datac1 + 1
                    
    datac3_nin = codec2.api.freedv_nin(datac3_freedv) * 2            
    if len(datac3_buffer) >= (datac3_nin):        
        datac3_audio = datac3_buffer[:datac3_nin]
        datac3_buffer = datac3_buffer[datac3_nin:]
        nbytes = codec2.api.freedv_rawdatarx(datac3_freedv, datac3_bytes_out, datac3_audio)  # demodulate audio    
        if nbytes == datac3_bytes_per_frame:
            rx_total_frames_datac3 = rx_total_frames_datac3 + 1
            rx_frames_datac3 = rx_frames_datac3 + 1

            if rx_frames_datac3 == N_FRAMES_PER_BURST:
                rx_frames_datac3 = 0
                rx_bursts_datac3 = rx_bursts_datac3 + 1   


    if rx_bursts_datac0 == N_BURSTS and rx_bursts_datac1 == N_BURSTS and rx_bursts_datac3 == N_BURSTS:
        receive = False 

# INFO IF WE REACHED TIMEOUT
if time.time() > timeout:
    print(f"TIMEOUT REACHED", file=sys.stderr)    
          
print(f"DATAC0: {rx_bursts_datac0}/{rx_total_frames_datac0} DATAC1: {rx_bursts_datac1}/{rx_total_frames_datac1} DATAC3: {rx_bursts_datac3}/{rx_total_frames_datac3}", file=sys.stderr)
