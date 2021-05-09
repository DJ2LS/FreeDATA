#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""
from PyQt5 import QtGui  # (the example applies equally well to PySide2)
import pyqtgraph as pg
import pyaudio
import numpy as np


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
parser.add_argument('--output', dest="DATA_OUTPUT", type=str)  
parser.add_argument('--audiooutput', dest="AUDIO_OUTPUT", default=0, type=int) 
parser.add_argument('--device', dest="HAMLIB_DEVICE_ID", default=0, type=int) 
parser.add_argument('--port', dest="HAMLIB_DEVICE_PORT", default=0, type=str) 


args = parser.parse_args()


print(args.HAMLIB_DEVICE_PORT)
print(args.HAMLIB_DEVICE_ID)


# Hamlib configuration
Hamlib.rig_set_debug(Hamlib.RIG_DEBUG_NONE)

my_rig = Hamlib.Rig(args.HAMLIB_DEVICE_ID) #311 ICOM, 2028 TS480, Hamlib.RIG_MODEL_DUMMY Dummy
my_rig.set_conf("rig_pathname", args.HAMLIB_DEVICE_PORT)

my_rig.set_conf("retry", "5")
my_rig.set_conf("serial_speed", "19200")

my_rig.set_conf("dtr_state", "OFF")
    #my_rig.set_conf("rts_state", "OFF")
my_rig.set_conf("ptt_type", "RTS")
    #my_rig.set_conf("ptt_type", "RIG_PTT_SERIAL_RTS")
    
my_rig.set_conf("serial_handshake", "None")
my_rig.set_conf("stop_bits", "1")
my_rig.set_conf("data_bits", "8")

my_rig.open()
  
# ------------------------------------------------------

N_BURSTS = args.N_BURSTS
N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
DATA_INPUT = args.DATA_INPUT
AUDIO_INPUT_DEVICE = args.AUDIO_INPUT
FREEDV_MODE = args.FREEDV_MODE
DEBUGGING_MODE = args.DEBUGGING_MODE

# 1024 good for mode 6
AUDIO_FRAMES_PER_BUFFER = 1024 
MODEM_SAMPLE_RATE = 8000








              
        #-------------------------------------------- LOAD FREEDV
             
libname = pathlib.Path().absolute() / "codec2/build_linux/src/libcodec2.so"
c_lib = ctypes.CDLL(libname)

        #--------------------------------------------CREATE PYAUDIO  INSTANCE
        
p = pyaudio.PyAudio()
        
        #--------------------------------------------GET SUPPORTED SAMPLE RATES FROM SOUND DEVICE
        
#AUDIO_SAMPLE_RATE_RX = int(p.get_device_info_by_index(AUDIO_INPUT_DEVICE)['defaultSampleRate'])

AUDIO_SAMPLE_RATE_RX = 48000
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

c_lib.freedv_set_frames_per_burst(freedv,N_FRAMES_PER_BURST)

        
total_n_bytes = 0
rx_total_frames = 0
rx_frames = 0
rx_bursts = 0
receive = True
while receive == True:
    time.sleep(0.01)

    
    if DATA_INPUT == "audio":
        
        nin = c_lib.freedv_nin(freedv)
        nin_converted = int(nin*(AUDIO_SAMPLE_RATE_RX/MODEM_SAMPLE_RATE))
        #if DEBUGGING_MODE == True:
            #print("-----------------------------")
            #print("NIN:  " + str(nin) + " [ " + str(nin_converted) + " ]")
        
        data_in = stream_rx.read(nin_converted,  exception_on_overflow = False)  
        data_in = audioop.ratecv(data_in,2,1,AUDIO_SAMPLE_RATE_RX, MODEM_SAMPLE_RATE, None) 
#        data_in = data_in[0].rstrip(b'\x00') 
        data_in = data_in[0]

    else:
        nin = c_lib.freedv_nin(freedv)*2
        data_in = sys.stdin.buffer.read(nin)

    #c_lib.freedv_rawdatarx.argtype = [ctypes.POINTER(ctypes.c_ubyte), bytes_out, data_in] # check if really neccessary 
    nbytes = c_lib.freedv_rawdatarx(freedv, bytes_out, data_in) # demodulate audio
    
    total_n_bytes = total_n_bytes + nbytes
    if DEBUGGING_MODE == True:
        if c_lib.freedv_get_rx_status(freedv) != 0:
            print("SYNC: " + str(c_lib.freedv_get_rx_status(freedv)))
            print(bytes(bytes_out))
            
        
    if nbytes == bytes_per_frame:
        rx_total_frames = rx_total_frames + 1
        rx_frames = rx_frames + 1

        if rx_frames == N_FRAMES_PER_BURST:
            rx_frames = 0
            rx_bursts = rx_bursts + 1
            #c_lib.freedv_set_sync(freedv,0) #this should be automatically done by c_lib.freedv_set_frames_per_burst(freedv,N_FRAMES_PER_BURST)
     
    if rx_bursts == N_BURSTS:
        receive = False
    
           
                   
print("------------------------------")
print("BURSTS: " + str(rx_bursts))
print("TOTAL RECEIVED BYTES: " + str(total_n_bytes)) 
print("RECEIVED FRAMES: " + str(rx_total_frames)) 

