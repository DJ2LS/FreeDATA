#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan  3 10:12:05 2021

@author: DJ2LS
"""
import pyaudio


import static




def read_audio():
    
        defaultFrames = static.DEFAULT_FRAMES
        audio_input_device = static.AUDIO_INPUT_DEVICE
        audio_output_device = static.AUDIO_OUTPUT_DEVICE 
        tx_sample_state = static.TX_SAMPLE_STATE
        rx_sample_state = static.RX_SAMPLE_STATE
        audio_sample_rate = static.AUDIO_SAMPLE_RATE
        modem_sample_rate = static.MODEM_SAMPLE_RATE
        audio_frames_per_buffer = static.AUDIO_FRAMES_PER_BUFFER
        audio_channels = static.AUDIO_CHANNELS
        format = pyaudio.paInt16
        stream = None
        
        n_max_modem_samples = 924
    
        p = pyaudio.PyAudio()  
        
        stream_rx = p.open(format=pyaudio.paInt16, 
                            channels=6,
                            rate=8000,
                            frames_per_buffer=924,
                            input=True,
                            input_device_index=1,
                            )
        while True:
            data_in = stream_rx.read(4096,  exception_on_overflow = False)
            static.AUDIO_BUFFER += data_in.strip(b'\x00')
        
            #print(static.AUDIO_BUFFER)
            #print(len(static.AUDIO_BUFFER))
