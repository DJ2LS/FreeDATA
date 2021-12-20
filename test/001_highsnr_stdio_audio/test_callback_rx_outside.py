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
sys.path.insert(0,'../..')
from tnc import codec2

#--------------------------------------------GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='FreeDATA audio test')
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



class Test():
    def __init__(self):
        self.N_BURSTS = args.N_BURSTS
        self.N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
        self.AUDIO_INPUT_DEVICE = args.AUDIO_INPUT_DEVICE
        self.MODE = codec2.FREEDV_MODE[args.FREEDV_MODE].value
        self.DEBUGGING_MODE = args.DEBUGGING_MODE
        self.TIMEOUT = args.TIMEOUT

        # AUDIO PARAMETERS
        self.AUDIO_FRAMES_PER_BUFFER = 2400*2  # <- consider increasing if you get nread_exceptions > 0
        self.MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
        self.AUDIO_SAMPLE_RATE_RX = 48000

        # make sure our resampler will work
        assert (self.AUDIO_SAMPLE_RATE_RX / self.MODEM_SAMPLE_RATE) == codec2.api.FDMDV_OS_48

        # check if we want to use an audio device then do an pyaudio init
        if self.AUDIO_INPUT_DEVICE != -1: 
            self.p = pyaudio.PyAudio()
            # auto search for loopback devices
            if self.AUDIO_INPUT_DEVICE == -2:
                loopback_list = []
                for dev in range(0,self.p.get_device_count()):
                    if 'Loopback: PCM' in self.p.get_device_info_by_index(dev)["name"]:
                        loopback_list.append(dev)
                if len(loopback_list) >= 2:
                    self.AUDIO_INPUT_DEVICE = loopback_list[0] #0  = RX   1 = TX
                    print(f"loopback_list rx: {loopback_list}", file=sys.stderr)
                else:
                    quit()
                    
            print(f"AUDIO INPUT DEVICE: {self.AUDIO_INPUT_DEVICE} DEVICE: {self.p.get_device_info_by_index(self.AUDIO_INPUT_DEVICE)['name']}  \
                    AUDIO SAMPLE RATE: {self.AUDIO_SAMPLE_RATE_RX}", file=sys.stderr)
            
            self.stream_rx = self.p.open(format=pyaudio.paInt16, 
                                    channels=1,
                                    rate=self.AUDIO_SAMPLE_RATE_RX,
                                    frames_per_buffer=self.AUDIO_FRAMES_PER_BUFFER,
                                    input=True,
                                    output=False,
                                    input_device_index=self.AUDIO_INPUT_DEVICE,
                                    stream_callback=self.callback
                                    ) 

        # open codec2 instance        
        self.freedv = cast(codec2.api.freedv_open(self.MODE), c_void_p)
        
        # get number of bytes per frame for mode
        self.bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(self.freedv)/8)
        
        self.bytes_out = create_string_buffer(self.bytes_per_frame * 2)
        
        codec2.api.freedv_set_frames_per_burst(self.freedv,self.N_FRAMES_PER_BURST)
        
        self.total_n_bytes = 0
        self.rx_total_frames = 0
        self.rx_frames = 0
        self.rx_bursts = 0
        self.rx_errors = 0
        self.nread_exceptions = 0
        self.timeout = time.time() + self.TIMEOUT
        self.receive = True
        self.audio_buffer = codec2.audio_buffer(self.AUDIO_FRAMES_PER_BUFFER*2)
        self.resampler = codec2.resampler()
        
        # Copy received 48 kHz to a file.  Listen to this file with:
        #   aplay -r 48000 -f S16_LE rx48_callback.raw
        # Corruption of this file is a good way to detect audio card issues
        self.frx = open("rx48_callback.raw", mode='wb')    
           
    def callback(self, data_in48k, frame_count, time_info, status):
        
        x = np.frombuffer(data_in48k, dtype=np.int16)
        x.tofile(self.frx)
        x = self.resampler.resample48_to_8(x)    
        self.audio_buffer.push(x)

        '''
        # when we have enough samples call FreeDV Rx
        nin = codec2.api.freedv_nin(self.freedv)
        while self.audio_buffer.nbuffer >= nin:

            # demodulate audio
            nbytes = codec2.api.freedv_rawdatarx(self.freedv, self.bytes_out, self.audio_buffer.buffer.ctypes)        
            self.audio_buffer.pop(nin)
            
            # call me on every loop!
            nin = codec2.api.freedv_nin(self.freedv)
           
            rx_status = codec2.api.freedv_get_rx_status(self.freedv)       
            if rx_status & codec2.api.FREEDV_RX_BIT_ERRORS:
                self.rx_errors = self.rx_errors + 1
            if self.DEBUGGING_MODE:        
              rx_status = codec2.api.rx_sync_flags_to_text[rx_status]
              print("nin: %5d rx_status: %4s naudio_buffer: %4d" % \
                    (nin,rx_status,self.audio_buffer.nbuffer), file=sys.stderr)

            if nbytes:
                self.total_n_bytes = self.total_n_bytes + nbytes
                
                if nbytes == self.bytes_per_frame:
                    self.rx_total_frames = self.rx_total_frames + 1
                    self.rx_frames = self.rx_frames + 1

                if self.rx_frames == self.N_FRAMES_PER_BURST:
                    self.rx_frames = 0
                    self.rx_bursts = self.rx_bursts + 1
                              
                if self.rx_bursts == self.N_BURSTS:
                    self.receive = False
            '''
        return (None, pyaudio.paContinue)

    def run_audio(self):
        try:                        
            print(f"starting pyaudio callback", file=sys.stderr)
            self.stream_rx.start_stream()
        except Exception as e:
            print(f"pyAudio error: {e}", file=sys.stderr) 
           

        while self.receive and time.time() < self.timeout:
            #time.sleep(1)
            # when we have enough samples call FreeDV Rx
            nin = codec2.api.freedv_nin(self.freedv)
            while self.audio_buffer.nbuffer >= nin:

                # demodulate audio
                nbytes = codec2.api.freedv_rawdatarx(self.freedv, self.bytes_out, self.audio_buffer.buffer.ctypes)        
                self.audio_buffer.pop(nin)
                
                # call me on every loop!
                nin = codec2.api.freedv_nin(self.freedv)
               
                rx_status = codec2.api.freedv_get_rx_status(self.freedv)       
                if rx_status & codec2.api.FREEDV_RX_BIT_ERRORS:
                    self.rx_errors = self.rx_errors + 1
                if self.DEBUGGING_MODE:        
                  rx_status = codec2.api.rx_sync_flags_to_text[rx_status]
                  print("nin: %5d rx_status: %4s naudio_buffer: %4d" % \
                        (nin,rx_status,self.audio_buffer.nbuffer), file=sys.stderr)

                if nbytes:
                    self.total_n_bytes = self.total_n_bytes + nbytes
                    
                    if nbytes == self.bytes_per_frame:
                        self.rx_total_frames = self.rx_total_frames + 1
                        self.rx_frames = self.rx_frames + 1

                    if self.rx_frames == self.N_FRAMES_PER_BURST:
                        self.rx_frames = 0
                        self.rx_bursts = self.rx_bursts + 1
                                  
                    if self.rx_bursts == self.N_BURSTS:
                        self.receive = False
        if time.time() >= self.timeout:
            print("TIMEOUT REACHED")
                
        if self.nread_exceptions:
            print("nread_exceptions %d - receive audio lost! Consider increasing Pyaudio frames_per_buffer..." %  \
                  self.nread_exceptions, file=sys.stderr)
        print(f"RECEIVED BURSTS: {self.rx_bursts} RECEIVED FRAMES: {self.rx_total_frames} RX_ERRORS: {self.rx_errors}", file=sys.stderr)
        self.frx.close()

        # cloese pyaudio instance
        self.stream_rx.close()
        self.p.terminate()
        
        
test = Test()
test.run_audio()        
