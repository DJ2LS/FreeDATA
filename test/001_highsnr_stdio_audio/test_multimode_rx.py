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
AUDIO_FRAMES_PER_BUFFER = 4096
MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
AUDIO_SAMPLE_RATE_RX = 48000
assert (AUDIO_SAMPLE_RATE_RX % MODEM_SAMPLE_RATE) == 0

BUF_SIZE = 160

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
receive = True


while receive and time.time() < timeout:
    if AUDIO_INPUT_DEVICE != -1: 
        
        data_in = stream_rx.read(AUDIO_FRAMES_PER_BUFFER,  exception_on_overflow = False)  
        data_in = audioop.ratecv(data_in,2,1,AUDIO_SAMPLE_RATE_RX, MODEM_SAMPLE_RATE, None) 

        datac0_buffer += data_in[0]
        datac1_buffer += data_in[0]
        datac3_buffer += data_in[0]


    else:
        data_in = sys.stdin.buffer.read(BUF_SIZE)
                    
        datac0_buffer += data_in
        datac1_buffer += data_in
        datac3_buffer += data_in
                    
        
    datac0_nin = codec2.api.freedv_nin(datac0_freedv) * 2                   
    if len(datac0_buffer) >= (datac0_nin):        
        nbytes = codec2.api.freedv_rawdatarx(datac0_freedv, datac0_bytes_out, datac0_buffer[:datac0_nin])  # demodulate audio
        datac0_buffer = datac0_buffer[datac0_nin:]
        if nbytes == datac0_bytes_per_frame:
            rx_total_frames_datac0 = rx_total_frames_datac0 + 1
            rx_frames_datac0 = rx_frames_datac0 + 1

            if rx_frames_datac0 == N_FRAMES_PER_BURST:
                rx_frames_datac0 = 0
                rx_bursts_datac0 = rx_bursts_datac0 + 1
               
       
    datac1_nin = codec2.api.freedv_nin(datac1_freedv) * 2            
    if len(datac1_buffer) >= (datac1_nin):        
        nbytes = codec2.api.freedv_rawdatarx(datac1_freedv, datac1_bytes_out, datac1_buffer[:datac1_nin])  # demodulate audio
        datac1_buffer = datac1_buffer[datac1_nin:]
        if nbytes == datac1_bytes_per_frame:
            rx_total_frames_datac1 = rx_total_frames_datac1 + 1
            rx_frames_datac1 = rx_frames_datac1 + 1

            if rx_frames_datac1 == N_FRAMES_PER_BURST:
                rx_frames_datac1 = 0
                rx_bursts_datac1 = rx_bursts_datac1 + 1
                    
    datac3_nin = codec2.api.freedv_nin(datac3_freedv) * 2            
    if len(datac3_buffer) >= (datac3_nin):        
        nbytes = codec2.api.freedv_rawdatarx(datac3_freedv, datac3_bytes_out, datac3_buffer[:datac3_nin])  # demodulate audio    
        datac3_buffer = datac3_buffer[datac3_nin:]
        if nbytes == datac3_bytes_per_frame:
            rx_total_frames_datac3 = rx_total_frames_datac3 + 1
            rx_frames_datac3 = rx_frames_datac3 + 1

            if rx_frames_datac3 == N_FRAMES_PER_BURST:
                rx_frames_datac3 = 0
                rx_bursts_datac3 = rx_bursts_datac3 + 1   


    if DEBUGGING_MODE:
        sync0 = codec2.api.freedv_get_rx_status(datac0_freedv)
        sync1 = codec2.api.freedv_get_rx_status(datac1_freedv)
        sync3 = codec2.api.freedv_get_rx_status(datac3_freedv)
        
        datac0_rxstatus = codec2.api.freedv_get_rx_status(datac0_freedv)
        datac0_state = codec2.api.rx_sync_flags_to_text[datac0_rxstatus]

        datac1_rxstatus = codec2.api.freedv_get_rx_status(datac1_freedv)
        datac1_state = codec2.api.rx_sync_flags_to_text[datac1_rxstatus]
        
        datac3_rxstatus = codec2.api.freedv_get_rx_status(datac3_freedv)
        datac3_state = codec2.api.rx_sync_flags_to_text[datac3_rxstatus]

        print(f"NIN0: {datac0_nin} STATE0: {datac3_state} | NIN1: {datac1_nin} STATE1: {datac1_state} | NIN3: {datac3_nin} STATE3: {datac3_state}", file=sys.stderr)


    if rx_bursts_datac0 == N_BURSTS and rx_bursts_datac1 == N_BURSTS and rx_bursts_datac3 == N_BURSTS:
        receive = False 

# INFO IF WE REACHED TIMEOUT
if time.time() > timeout:
    print(f"TIMEOUT REACHED", file=sys.stderr)    
          
print(f"DATAC0: {rx_bursts_datac0}/{rx_total_frames_datac0} DATAC1: {rx_bursts_datac1}/{rx_total_frames_datac1} DATAC3: {rx_bursts_datac3}/{rx_total_frames_datac3}", file=sys.stderr)

