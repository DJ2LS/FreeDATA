#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 17:47:32 2020

@author: DJ2LS
"""


import pyaudio
import audioop
import logging


class Audio():
    
    def __init__(self,        
        defaultFrames = 1024 * 8,
        audio_input_device=2,
        audio_output_device=0,    
        tx_sample_state = None,
        rx_sample_state = None,
        audio_sample_rate=48000,
        modem_sample_rate=8000,
        frames_per_buffer=1024,
        audio_channels=1, 
        #format = pyaudio.paInt16,
        stream = None,
        ):
        
        self.p = pyaudio.PyAudio()
        self.defaultFrames = defaultFrames
        self.audio_input_device = audio_input_device
        self.audio_output_device = audio_output_device 
        self.tx_sample_state = tx_sample_state
        self.rx_sample_state = rx_sample_state
        self.audio_sample_rate = audio_sample_rate
        self.modem_sample_rate = modem_sample_rate
        self.frames_per_buffer = frames_per_buffer
        self.audio_channels = audio_channels
        self.format = pyaudio.paInt16
        self.stream = None
        
        logging.info("AUDIO Initialized")
    
    
    # PLAY MODULATED AUDIO     
    def Play(self, modulation):
               
        stream_tx = self.p.open(format=self.format, 
                            channels=self.audio_channels,
                            rate=self.audio_sample_rate,
                            frames_per_buffer=self.frames_per_buffer,
                            output=True,
                            output_device_index=self.audio_output_device,
                            )     
        
        audio = audioop.ratecv(modulation,2,1,self.modem_sample_rate, self.audio_sample_rate, self.tx_sample_state)                                                   
        stream_tx.write(audio[0])
        stream_tx.close()
        #self.p.terminate()        
    
    
    # RECORD AUDIO
    def Record(self):
        
        stream_rx = self.p.open(format=self.format, 
                            channels=self.audio_channels,
                            rate=self.audio_sample_rate,
                            frames_per_buffer=self.frames_per_buffer, #modem.get_n_max_modem_samples()
                            input=True,
                            input_device_index=self.audio_input_device,
                            )        
        
        #audio = audioop.ratecv(modulation,2,1,modem_sample_rate, audio_sample_rate, tx_sample_state)                                                   
        #stream.read(audio[0])
        data = stream_rx.read(self.defaultFrames)
        data = audioop.ratecv(data,2,1,self.audio_sample_rate, self.modem_sample_rate, self.rx_sample_state)
        #stream_rx.close()
        #self.p.terminate()
        return data