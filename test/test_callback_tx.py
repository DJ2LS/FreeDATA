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
import queue
import numpy as np
sys.path.insert(0,'..')
from tnc import codec2

#--------------------------------------------GET PARAMETER INPUTS  
parser = argparse.ArgumentParser(description='FreeDATA audio test')
parser.add_argument('--bursts', dest="N_BURSTS", default=1, type=int)
parser.add_argument('--framesperburst', dest="N_FRAMES_PER_BURST", default=1, type=int)
parser.add_argument('--delay', dest="DELAY_BETWEEN_BURSTS", default=500, type=int)
parser.add_argument('--mode', dest="FREEDV_MODE", type=str, choices=['datac0', 'datac1', 'datac3'])
parser.add_argument('--audiodev', dest="AUDIO_OUTPUT_DEVICE", default=-1, type=int,
                    help="audio device number to use, use -2 to automatically select a loopback device")  
parser.add_argument('--list', dest="LIST", action="store_true", help="list audio devices by number and exit")  
parser.add_argument('--testframes', dest="TESTFRAMES", action="store_true", default=False, help="generate testframes")  

args = parser.parse_args()

if args.LIST:
    p = pyaudio.PyAudio()
    for dev in range(0,p.get_device_count()):
        print("audiodev: ", dev, p.get_device_info_by_index(dev)["name"])
    quit()



class Test():
    def __init__(self):

        self.dataqueue = queue.Queue()
        self.N_BURSTS = args.N_BURSTS
        self.N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
        self.AUDIO_OUTPUT_DEVICE = args.AUDIO_OUTPUT_DEVICE
        self.MODE = codec2.FREEDV_MODE[args.FREEDV_MODE].value
        self.DELAY_BETWEEN_BURSTS = args.DELAY_BETWEEN_BURSTS/1000

        # AUDIO PARAMETERS
        self.AUDIO_FRAMES_PER_BUFFER = 2400  # <- consider increasing if you get nread_exceptions > 0
        self.MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
        self.AUDIO_SAMPLE_RATE_TX = 48000

        # make sure our resampler will work
        assert (self.AUDIO_SAMPLE_RATE_TX / self.MODEM_SAMPLE_RATE) == codec2.api.FDMDV_OS_48

        
        self.transmit = True

        self.resampler = codec2.resampler()
        
        
        # check if we want to use an audio device then do an pyaudio init
        if self.AUDIO_OUTPUT_DEVICE != -1: 
            self.p = pyaudio.PyAudio()
            # auto search for loopback devices
            if self.AUDIO_OUTPUT_DEVICE == -2:
                loopback_list = []
                for dev in range(0,self.p.get_device_count()):
                    if 'Loopback: PCM' in self.p.get_device_info_by_index(dev)["name"]:
                        loopback_list.append(dev)
                if len(loopback_list) >= 2:
                    self.AUDIO_OUTPUT_DEVICE = loopback_list[0] #0  = RX   1 = TX
                    print(f"loopback_list rx: {loopback_list}", file=sys.stderr)
                else:
                    quit()
                    
            print(f"AUDIO OUTPUT DEVICE: {self.AUDIO_OUTPUT_DEVICE} DEVICE: {self.p.get_device_info_by_index(self.AUDIO_OUTPUT_DEVICE)['name']}  \
                    AUDIO SAMPLE RATE: {self.AUDIO_SAMPLE_RATE_TX}", file=sys.stderr)
            
            self.stream_tx = self.p.open(format=pyaudio.paInt16, 
                                    channels=1,
                                    rate=self.AUDIO_SAMPLE_RATE_TX,
                                    frames_per_buffer=self.AUDIO_FRAMES_PER_BUFFER,
                                    input=False,
                                    output=True,
                                    output_device_index=self.AUDIO_OUTPUT_DEVICE,
                                    stream_callback=self.callback
                                    ) 

        # open codec2 instance        
        self.freedv = cast(codec2.api.freedv_open(self.MODE), c_void_p)
        
        # get number of bytes per frame for mode
        self.bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(self.freedv)/8)
        
        self.bytes_out = create_string_buffer(self.bytes_per_frame)
        
        codec2.api.freedv_set_frames_per_burst(self.freedv,self.N_FRAMES_PER_BURST)
        
        
        # Copy received 48 kHz to a file.  Listen to this file with:
        #   aplay -r 48000 -f S16_LE rx48_callback.raw
        # Corruption of this file is a good way to detect audio card issues
        self.ftx = open("tx48_callback.raw", mode='wb')    

        # data binary string
        if args.TESTFRAMES:
            self.data_out = bytearray(14)
            self.data_out[:1]   = bytes([255])
            self.data_out[1:2]  = bytes([1])
            self.data_out[2:]  = b'HELLO WORLD'
            
        else:
            self.data_out = b'HELLO WORLD!'

           
    def callback(self, data_in48k, frame_count, time_info, status):
        
        data_out48k = self.dataqueue.get()
        return (data_out48k, pyaudio.paContinue)

    def run_audio(self):
        try:                        
            print(f"starting pyaudio callback", file=sys.stderr)
            self.stream_tx.start_stream()
        except Exception as e:
            print(f"pyAudio error: {e}", file=sys.stderr) 
           
        sheeps = 0
        while self.transmit:
            time.sleep(1)
            sheeps = sheeps + 1
            print(f"counting sheeps...{sheeps}")


        
        self.ftx.close()

        # close pyaudio instance
        self.stream_tx.close()
        self.p.terminate()
     
    def create_modulation(self):
    
        # open codec2 instance        
        freedv = cast(codec2.api.freedv_open(self.MODE), c_void_p)

        # get number of bytes per frame for mode
        bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(freedv)/8)
        payload_bytes_per_frame = bytes_per_frame -2

        # init buffer for data
        n_tx_modem_samples = codec2.api.freedv_get_n_tx_modem_samples(freedv)
        mod_out = create_string_buffer(n_tx_modem_samples * 2)

        # init buffer for preample
        n_tx_preamble_modem_samples = codec2.api.freedv_get_n_tx_preamble_modem_samples(freedv)
        mod_out_preamble = create_string_buffer(n_tx_preamble_modem_samples * 2)

        # init buffer for postamble
        n_tx_postamble_modem_samples = codec2.api.freedv_get_n_tx_postamble_modem_samples(freedv)
        mod_out_postamble = create_string_buffer(n_tx_postamble_modem_samples * 2)

        # create buffer for data
        buffer = bytearray(payload_bytes_per_frame) # use this if CRC16 checksum is required ( DATA1-3)
        buffer[:len(self.data_out)] = self.data_out # set buffersize to length of data which will be send

        # create crc for data frame - we are using the crc function shipped with codec2 to avoid 
        # crc algorithm incompatibilities
        crc = ctypes.c_ushort(codec2.api.freedv_gen_crc16(bytes(buffer), payload_bytes_per_frame))     # generate CRC16
        crc = crc.value.to_bytes(2, byteorder='big') # convert crc to 2 byte hex string
        buffer += crc        # append crc16 to buffer    

        print(f"TOTAL BURSTS: {self.N_BURSTS} TOTAL FRAMES_PER_BURST: {self.N_FRAMES_PER_BURST}", file=sys.stderr)

        for i in range(1,self.N_BURSTS+1):

            # write preamble to txbuffer
            codec2.api.freedv_rawdatapreambletx(freedv, mod_out_preamble)
            txbuffer = bytes(mod_out_preamble)

            # create modulaton for N = FRAMESPERBURST and append it to txbuffer
            for n in range(1,self.N_FRAMES_PER_BURST+1):

                data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
                codec2.api.freedv_rawdatatx(freedv,mod_out,data) # modulate DATA and save it into mod_out pointer 

                txbuffer += bytes(mod_out)
                
                print(f" GENERATING TX BURST: {i}/{self.N_BURSTS} FRAME: {n}/{self.N_FRAMES_PER_BURST}", file=sys.stderr)
            
            # append postamble to txbuffer          
            codec2.api.freedv_rawdatapostambletx(freedv, mod_out_postamble)
            txbuffer += bytes(mod_out_postamble)

            # append a delay between bursts as audio silence
            samples_delay = int(self.MODEM_SAMPLE_RATE*self.DELAY_BETWEEN_BURSTS)
            mod_out_silence = create_string_buffer(samples_delay*2)
            txbuffer += bytes(mod_out_silence)
            print(f"samples_delay: {samples_delay} DELAY_BETWEEN_BURSTS: {self.DELAY_BETWEEN_BURSTS}", file=sys.stderr)

            # resample up to 48k (resampler works on np.int16)
            x = np.frombuffer(txbuffer, dtype=np.int16)
            txbuffer_48k = self.resampler.resample8_to_48(x)

            # split modualted audio to chunks
            #https://newbedev.com/how-to-split-a-byte-string-into-separate-bytes-in-python
            txbuffer_48k = bytes(txbuffer_48k)
            chunk = [txbuffer_48k[i:i+self.AUDIO_FRAMES_PER_BUFFER*2] for i in range(0, len(txbuffer_48k), self.AUDIO_FRAMES_PER_BUFFER*2)]
            # add modulated chunks to fifo buffer
            for c in chunk:
                # if data is shorter than the expcected audio frames per buffer we need to append 0
                # to prevent the callback from stucking/crashing
                if len(c) < self.AUDIO_FRAMES_PER_BUFFER*2:
                    c += bytes(self.AUDIO_FRAMES_PER_BUFFER*2 - len(c))
                self.dataqueue.put(c)

              
        
test = Test()
test.create_modulation()
test.run_audio()        
