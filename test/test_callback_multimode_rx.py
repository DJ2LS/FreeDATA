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
from tnc import codec2

#--------------------------------------------GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='FreeDATA audio test')
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



class Test():
    def __init__(self):
        self.N_BURSTS = args.N_BURSTS
        self.N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
        self.AUDIO_INPUT_DEVICE = args.AUDIO_INPUT_DEVICE
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
        self.datac0_freedv = cast(codec2.api.freedv_open(codec2.api.FREEDV_MODE_DATAC0), c_void_p)
        self.datac0_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(self.datac0_freedv)/8)
        self.datac0_bytes_out = create_string_buffer(self.datac0_bytes_per_frame)
        codec2.api.freedv_set_frames_per_burst(self.datac0_freedv,self.N_FRAMES_PER_BURST)
        self.datac0_buffer = codec2.audio_buffer(2*self.AUDIO_FRAMES_PER_BUFFER)

        self.datac1_freedv = cast(codec2.api.freedv_open(codec2.api.FREEDV_MODE_DATAC1), c_void_p)
        self.datac1_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(self.datac1_freedv)/8)
        self.datac1_bytes_out = create_string_buffer(self.datac1_bytes_per_frame)
        codec2.api.freedv_set_frames_per_burst(self.datac1_freedv,self.N_FRAMES_PER_BURST)
        self.datac1_buffer = codec2.audio_buffer(2*self.AUDIO_FRAMES_PER_BUFFER)

        self.datac3_freedv = cast(codec2.api.freedv_open(codec2.api.FREEDV_MODE_DATAC3), c_void_p)
        self.datac3_bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(self.datac3_freedv)/8)
        self.datac3_bytes_out = create_string_buffer(self.datac3_bytes_per_frame)
        codec2.api.freedv_set_frames_per_burst(self.datac3_freedv,self.N_FRAMES_PER_BURST)
        self.datac3_buffer = codec2.audio_buffer(2*self.AUDIO_FRAMES_PER_BUFFER)



        # SET COUNTERS
        self.rx_total_frames_datac0 = 0
        self.rx_frames_datac0 = 0
        self.rx_bursts_datac0 = 0

        self.rx_total_frames_datac1 = 0
        self.rx_frames_datac1 = 0
        self.rx_bursts_datac1 = 0

        self.rx_total_frames_datac3 = 0
        self.rx_frames_datac3 = 0
        self.rx_bursts_datac3 = 0

        self.rx_errors = 0
        self.nread_exceptions = 0
        self.timeout = time.time() + self.TIMEOUT
        self.receive = True
        self.resampler = codec2.resampler()
        
        # Copy received 48 kHz to a file.  Listen to this file with:
        #   aplay -r 48000 -f S16_LE rx48_callback.raw
        # Corruption of this file is a good way to detect audio card issues
        self.frx = open("rx48_callback_multimode.raw", mode='wb')    
        
        
        # initial nin values        
        self.datac0_nin = codec2.api.freedv_nin(self.datac0_freedv)               
        self.datac1_nin = codec2.api.freedv_nin(self.datac1_freedv)               
        self.datac3_nin = codec2.api.freedv_nin(self.datac3_freedv)


        self.LOGGER_THREAD = threading.Thread(target=self.print_stats, name="LOGGER_THREAD")
        self.LOGGER_THREAD.start()
                   
           
    def callback(self, data_in48k, frame_count, time_info, status):
        x = np.frombuffer(data_in48k, dtype=np.int16)
        x.tofile(self.frx)
        x = self.resampler.resample48_to_8(x)    

        self.datac0_buffer.push(x)
        self.datac1_buffer.push(x)
        self.datac3_buffer.push(x)
    
    
        while self.datac0_buffer.nbuffer >= self.datac0_nin:        
            # demodulate audio
            nbytes = codec2.api.freedv_rawdatarx(self.datac0_freedv, self.datac0_bytes_out, self.datac0_buffer.buffer.ctypes)
            self.datac0_buffer.pop(self.datac0_nin)
            self.datac0_nin = codec2.api.freedv_nin(self.datac0_freedv)
            if nbytes == self.datac0_bytes_per_frame:
                self.rx_total_frames_datac0 = self.rx_total_frames_datac0 + 1
                self.rx_frames_datac0 = self.rx_frames_datac0 + 1

                if self.rx_frames_datac0 == self.N_FRAMES_PER_BURST:
                    self.rx_frames_datac0 = 0
                    self.rx_bursts_datac0 = self.rx_bursts_datac0 + 1

           
        while self.datac1_buffer.nbuffer >= self.datac1_nin:
            # demodulate audio
            nbytes = codec2.api.freedv_rawdatarx(self.datac1_freedv, self.datac1_bytes_out, self.datac1_buffer.buffer.ctypes)
            self.datac1_buffer.pop(self.datac1_nin)
            self.datac1_nin = codec2.api.freedv_nin(self.datac1_freedv)
            if nbytes == self.datac1_bytes_per_frame:
                self.rx_total_frames_datac1 = self.rx_total_frames_datac1 + 1
                self.rx_frames_datac1 = self.rx_frames_datac1 + 1

                if self.rx_frames_datac1 == self.N_FRAMES_PER_BURST:
                    self.rx_frames_datac1 = 0
                    self.rx_bursts_datac1 = self.rx_bursts_datac1 + 1

                        
        while self.datac3_buffer.nbuffer >= self.datac3_nin:
            # demodulate audio    
            nbytes = codec2.api.freedv_rawdatarx(self.datac3_freedv, self.datac3_bytes_out, self.datac3_buffer.buffer.ctypes)
            self.datac3_buffer.pop(self.datac3_nin)
            self.datac3_nin = codec2.api.freedv_nin(self.datac3_freedv)
            if nbytes == self.datac3_bytes_per_frame:
                self.rx_total_frames_datac3 = self.rx_total_frames_datac3 + 1
                self.rx_frames_datac3 = self.rx_frames_datac3 + 1

                if self.rx_frames_datac3 == self.N_FRAMES_PER_BURST:
                    self.rx_frames_datac3 = 0
                    self.rx_bursts_datac3 = self.rx_bursts_datac3 + 1   


        if (self.rx_bursts_datac0 and self.rx_bursts_datac1 and self.rx_bursts_datac3) == self.N_BURSTS:
            self.receive = False
             
        return (None, pyaudio.paContinue)
    
    def print_stats(self):
        while self.receive:
            time.sleep(0.01)
            if self.DEBUGGING_MODE:
                self.datac0_rxstatus = codec2.api.freedv_get_rx_status(self.datac0_freedv)
                self.datac0_rxstatus = codec2.api.rx_sync_flags_to_text[self.datac0_rxstatus]

                self.datac1_rxstatus = codec2.api.freedv_get_rx_status(self.datac1_freedv)
                self.datac1_rxstatus = codec2.api.rx_sync_flags_to_text[self.datac1_rxstatus]
                
                self.datac3_rxstatus = codec2.api.freedv_get_rx_status(self.datac3_freedv)
                self.datac3_rxstatus = codec2.api.rx_sync_flags_to_text[self.datac3_rxstatus]

                print("NIN0: %5d RX_STATUS0: %4s NIN1: %5d RX_STATUS1: %4s NIN3: %5d RX_STATUS3: %4s" % \
                      (self.datac0_nin, self.datac0_rxstatus, self.datac1_nin, self.datac1_rxstatus, self.datac3_nin, self.datac3_rxstatus),
                      file=sys.stderr)
                  
              
    def run_audio(self):
        try:                        
            print(f"starting pyaudio callback", file=sys.stderr)
            self.stream_rx.start_stream()
        except Exception as e:
            print(f"pyAudio error: {e}", file=sys.stderr) 
           

        while self.receive and time.time() < self.timeout:
            time.sleep(1)

        if time.time() >= self.timeout and self.stream_rx.is_active():
            print("TIMEOUT REACHED")
            self.receive = False
                
        if self.nread_exceptions:
            print("nread_exceptions %d - receive audio lost! Consider increasing Pyaudio frames_per_buffer..." %  \
                  self.nread_exceptions, file=sys.stderr)

        print(f"DATAC0: {self.rx_bursts_datac0}/{self.rx_total_frames_datac0} DATAC1: {self.rx_bursts_datac1}/{self.rx_total_frames_datac1} DATAC3: {self.rx_bursts_datac3}/{self.rx_total_frames_datac3}", file=sys.stderr)
        self.frx.close()

        # cloese pyaudio instance
        self.stream_rx.close()
        self.p.terminate()
        
        
test = Test()
test.run_audio()        
