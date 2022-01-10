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
from tnc import codec2
import numpy as np

#--------------------------------------------GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--bursts', dest="N_BURSTS", default=1, type=int)
parser.add_argument('--framesperburst', dest="N_FRAMES_PER_BURST", default=1, type=int)
parser.add_argument('--audiodev', dest="AUDIO_INPUT_DEVICE", default=-1, type=int, help="audio device number to use")  
parser.add_argument('--debug', dest="DEBUGGING_MODE", action="store_true") 
parser.add_argument('--list', dest="LIST", action="store_true", help="list audio devices by number and exit")  
parser.add_argument('--timeout', dest="TIMEOUT", default=10, type=int, help="Timeout (seconds) before test ends")  

args = parser.parse_args()

if args.LIST:
    p = pyaudio.PyAudio()
    for dev in range(0,p.get_device_count()):
        print("audiodev: ", dev, p.get_device_info_by_index(dev)["name"])
    quit()

N_BURSTS = args.N_BURSTS
N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
AUDIO_INPUT_DEVICE = args.AUDIO_INPUT_DEVICE
DEBUGGING_MODE = args.DEBUGGING_MODE
TIMEOUT = args.TIMEOUT

# AUDIO PARAMETERS
AUDIO_FRAMES_PER_BUFFER = 2400*2
MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
AUDIO_SAMPLE_RATE_RX = 48000
# make sure our resampler will work
assert (AUDIO_SAMPLE_RATE_RX / MODEM_SAMPLE_RATE) == codec2.api.FDMDV_OS_48

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

# time meassurement
time_start_datac0 = 0
time_end_datac0 = 0
time_start_datac1 = 0
time_end_datac1 = 0
time_start_datac3 = 0
time_end_datac3 = 0
time_needed_datac0 = 0
time_needed_datac1 = 0
time_needed_datac3 = 0

# open codec2 instance        
datac0_freedv = cast(codec2.api.freedv_open(codec2.api.FREEDV_MODE_DATAC0), c_void_p)
datac0_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(datac0_freedv)/8)
datac0_bytes_out = create_string_buffer(datac0_bytes_per_frame)
codec2.api.freedv_set_frames_per_burst(datac0_freedv,N_FRAMES_PER_BURST)
datac0_buffer = codec2.audio_buffer(2*AUDIO_FRAMES_PER_BUFFER)

datac1_freedv = cast(codec2.api.freedv_open(codec2.api.FREEDV_MODE_DATAC1), c_void_p)
datac1_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(datac1_freedv)/8)
datac1_bytes_out = create_string_buffer(datac1_bytes_per_frame)
codec2.api.freedv_set_frames_per_burst(datac1_freedv,N_FRAMES_PER_BURST)
datac1_buffer = codec2.audio_buffer(2*AUDIO_FRAMES_PER_BUFFER)

datac3_freedv = cast(codec2.api.freedv_open(codec2.api.FREEDV_MODE_DATAC3), c_void_p)
datac3_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(datac3_freedv)/8)
datac3_bytes_out = create_string_buffer(datac3_bytes_per_frame)
codec2.api.freedv_set_frames_per_burst(datac3_freedv,N_FRAMES_PER_BURST)
datac3_buffer = codec2.audio_buffer(2*AUDIO_FRAMES_PER_BUFFER)

resampler = codec2.resampler()

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
            
    print(f"AUDIO INPUT DEVICE: {AUDIO_INPUT_DEVICE} DEVICE: {p.get_device_info_by_index(AUDIO_INPUT_DEVICE)['name']} AUDIO SAMPLE RATE: {AUDIO_SAMPLE_RATE_RX}", file=sys.stderr)
    stream_rx = p.open(format=pyaudio.paInt16,
                                     channels=1,
                                     rate=AUDIO_SAMPLE_RATE_RX,
                                     frames_per_buffer=AUDIO_FRAMES_PER_BUFFER,
                                     input=True,
                                     input_device_index=AUDIO_INPUT_DEVICE
                                     )
                                     

timeout = time.time() + TIMEOUT
print(time.time(),TIMEOUT, timeout)
receive = True
nread_exceptions = 0

# initial nin values        
datac0_nin = codec2.api.freedv_nin(datac0_freedv)               
datac1_nin = codec2.api.freedv_nin(datac1_freedv)               
datac3_nin = codec2.api.freedv_nin(datac3_freedv)               

def print_stats(time_needed_datac0, time_needed_datac1, time_needed_datac3):
    if DEBUGGING_MODE:
        datac0_rxstatus = codec2.api.freedv_get_rx_status(datac0_freedv)
        datac0_rxstatus = codec2.api.rx_sync_flags_to_text[datac0_rxstatus]

        datac1_rxstatus = codec2.api.freedv_get_rx_status(datac1_freedv)
        datac1_rxstatus = codec2.api.rx_sync_flags_to_text[datac1_rxstatus]
        
        datac3_rxstatus = codec2.api.freedv_get_rx_status(datac3_freedv)
        datac3_rxstatus = codec2.api.rx_sync_flags_to_text[datac3_rxstatus]

        print("NIN0: %5d RX_STATUS0: %4s TIME: %4s | NIN1: %5d RX_STATUS1: %4s TIME: %4s | NIN3: %5d RX_STATUS3: %4s TIME: %4s" % \
              (datac0_nin, datac0_rxstatus, round(time_needed_datac0, 4), datac1_nin, datac1_rxstatus, round(time_needed_datac1, 4) ,datac3_nin, datac3_rxstatus, round(time_needed_datac3, 4)),
              file=sys.stderr)

while receive and time.time() < timeout:
    if AUDIO_INPUT_DEVICE != -1:         
        try:
            data_in48k = stream_rx.read(AUDIO_FRAMES_PER_BUFFER, exception_on_overflow = True)
        except OSError as err:
            print(err, file=sys.stderr)
            if str(err).find("Input overflowed") != -1:
                nread_exceptions += 1
            if str(err).find("Stream closed") != -1:
                print("Ending....")
                receive = False
    else:
        data_in48k = sys.stdin.buffer.read(AUDIO_FRAMES_PER_BUFFER*2)
                    
    # insert samples in buffer
    x = np.frombuffer(data_in48k, dtype=np.int16)    
    if len(x) != AUDIO_FRAMES_PER_BUFFER:
        print("len(x)",len(x))
        receive = False
    x = resampler.resample48_to_8(x)
        
    datac0_buffer.push(x)
    datac1_buffer.push(x)
    datac3_buffer.push(x)
    print_something = False
                   
    while datac0_buffer.nbuffer >= datac0_nin:        
        # demodulate audio
        time_start_datac0 = time.time()
        nbytes = codec2.api.freedv_rawdatarx(datac0_freedv, datac0_bytes_out, datac0_buffer.buffer.ctypes)
        time_end_datac0 = time.time()
        datac0_buffer.pop(datac0_nin)
        datac0_nin = codec2.api.freedv_nin(datac0_freedv)
        if nbytes == datac0_bytes_per_frame:
            rx_total_frames_datac0 = rx_total_frames_datac0 + 1
            rx_frames_datac0 = rx_frames_datac0 + 1

            if rx_frames_datac0 == N_FRAMES_PER_BURST:
                rx_frames_datac0 = 0
                rx_bursts_datac0 = rx_bursts_datac0 + 1
        time_needed_datac0 = time_end_datac0 - time_start_datac0
        print_stats(time_needed_datac0, time_needed_datac1, time_needed_datac3)
       
    while datac1_buffer.nbuffer >= datac1_nin:
        # demodulate audio
        time_start_datac1 = time.time()
        nbytes = codec2.api.freedv_rawdatarx(datac1_freedv, datac1_bytes_out, datac1_buffer.buffer.ctypes)
        time_end_datac1 = time.time()
        datac1_buffer.pop(datac1_nin)
        datac1_nin = codec2.api.freedv_nin(datac1_freedv)
        if nbytes == datac1_bytes_per_frame:
            rx_total_frames_datac1 = rx_total_frames_datac1 + 1
            rx_frames_datac1 = rx_frames_datac1 + 1

            if rx_frames_datac1 == N_FRAMES_PER_BURST:
                rx_frames_datac1 = 0
                rx_bursts_datac1 = rx_bursts_datac1 + 1
        time_needed_datac1 = time_end_datac1 - time_start_datac1
        print_stats(time_needed_datac0, time_needed_datac1, time_needed_datac3)
                    
    while datac3_buffer.nbuffer >= datac3_nin:
        # demodulate audio    
        time_start_datac3 = time.time()
        nbytes = codec2.api.freedv_rawdatarx(datac3_freedv, datac3_bytes_out, datac3_buffer.buffer.ctypes)
        time_end_datac3 = time.time()
        datac3_buffer.pop(datac3_nin)
        datac3_nin = codec2.api.freedv_nin(datac3_freedv)
        if nbytes == datac3_bytes_per_frame:
            rx_total_frames_datac3 = rx_total_frames_datac3 + 1
            rx_frames_datac3 = rx_frames_datac3 + 1

            if rx_frames_datac3 == N_FRAMES_PER_BURST:
                rx_frames_datac3 = 0
                rx_bursts_datac3 = rx_bursts_datac3 + 1   
        time_needed_datac3 = time_end_datac3 - time_start_datac3
        print_stats(time_needed_datac0, time_needed_datac1, time_needed_datac3)

    if rx_bursts_datac0 == N_BURSTS and rx_bursts_datac1 == N_BURSTS and rx_bursts_datac3 == N_BURSTS:
        receive = False 

if nread_exceptions:
    print("nread_exceptions %d - receive audio lost! Consider increasing Pyaudio frames_per_buffer..." %  \
          nread_exceptions, file=sys.stderr)
# INFO IF WE REACHED TIMEOUT
if time.time() > timeout:
    print(f"TIMEOUT REACHED", file=sys.stderr)    
          




print(f"DATAC0: {rx_bursts_datac0}/{rx_total_frames_datac0} DATAC1: {rx_bursts_datac1}/{rx_total_frames_datac1} DATAC3: {rx_bursts_datac3}/{rx_total_frames_datac3}", file=sys.stderr)

if AUDIO_INPUT_DEVICE != -1: 
    stream_rx.close()
    p.terminate()
