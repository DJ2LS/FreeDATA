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
import audioop
import sys
import logging


import static
import arq

#arq = arq.ARQ()



class RF():
    
    def __init__(self):
        
        #self.p = pyaudio.PyAudio()
        #self.defaultFrames = static.DEFAULT_FRAMES
        #self.audio_input_device = static.AUDIO_INPUT_DEVICE
        #self.audio_output_device = static.AUDIO_OUTPUT_DEVICE 
        #self.tx_sample_state = static.TX_SAMPLE_STATE
        #self.rx_sample_state = static.RX_SAMPLE_STATE
        #self.audio_sample_rate = static.AUDIO_SAMPLE_RATE
        #self.modem_sample_rate = static.MODEM_SAMPLE_RATE
        #self.audio_frames_per_buffer = static.AUDIO_FRAMES_PER_BUFFER
        #self.audio_channels = static.AUDIO_CHANNELS
        #self.format = pyaudio.paInt16
        #self.stream = None
              
             
        libname = pathlib.Path().absolute() / "codec2/build_linux/src/libcodec2.so"
        self.c_lib = ctypes.CDLL(libname)
        
        #self.mode = static.FREEDV_MODE # define mode
          
        #self.freedv = self.c_lib.freedv_open(self.mode)
        #self.bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(self.freedv)/8)
        #self.payload_per_frame = self.bytes_per_frame -2        
        #self.n_tx_modem_samples = self.c_lib.freedv_get_n_tx_modem_samples(self.freedv)*2 #get n_tx_modem_samples which defines the size of the modulation object
        #self.n_max_modem_samples = self.c_lib.freedv_get_n_max_modem_samples(self.freedv)
        #self.n_nom_modem_samples = self.c_lib.freedv_get_n_nom_modem_samples(self.freedv)
        #self.nin = self.c_lib.freedv_nin(self.freedv)

        #static.FREEDV_BYTES_PER_FRAME = self.bytes_per_frame
        #static.FREEDV_PAYLOAD_PER_FRAME = self.payload_per_frame

        #print(static.AUDIO_INPUT_DEVICE)
        # Open Audio Channel once
        self.p = pyaudio.PyAudio()
        self.stream_rx = self.p.open(format=pyaudio.paInt16, 
                            channels=static.AUDIO_CHANNELS,
                            rate=static.AUDIO_SAMPLE_RATE,
                            frames_per_buffer=4096,
                            input=True,
                            input_device_index=static.AUDIO_INPUT_DEVICE,
                            ) 
        

    # GET DATA AND MODULATE IT
    
    def Transmit(self,mode,data_out):
        static.MODEM_RECEIVE = False
        self.c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
        freedv = self.c_lib.freedv_open(mode)
        bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(freedv)/8)
        payload_per_frame = bytes_per_frame -2
        n_nom_modem_samples = self.c_lib.freedv_get_n_nom_modem_samples(freedv)
        n_tx_modem_samples = self.c_lib.freedv_get_n_tx_modem_samples(freedv)*2 #get n_tx_modem_samples which defines the size of the modulation object

          
        mod_out = ctypes.c_short * n_tx_modem_samples
        mod_out = mod_out()
        
    
        data_list = [data_out[i:i+payload_per_frame] for i in range(0, len(data_out), payload_per_frame)] # split incomming bytes to size of 30bytes, create a list and loop through it  
        data_list_length = len(data_list)
        for i in range(data_list_length): # LOOP THROUGH DATA LIST
            
            if mode < 10: # don't generate CRC16 for modes 0 - 9
            
                buffer = bytearray(bytes_per_frame) # use this if no CRC16 checksum is required
                buffer[:len(data_list[i])] = data_list[i] # set buffersize to length of data which will be send
                
            if mode >= 10: #generate CRC16 for modes 10-12..
                
                buffer = bytearray(payload_per_frame) # use this if CRC16 checksum is required ( DATA1-3)
                buffer[:len(data_list[i])] = data_list[i] # set buffersize to length of data which will be send

                crc = ctypes.c_ushort(self.c_lib.freedv_gen_crc16(bytes(buffer), payload_per_frame))     # generate CRC16
                crc = crc.value.to_bytes(2, byteorder='big') # convert crc to 2 byte hex string
                buffer += crc        # append crc16 to buffer
                
                
            data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
            
            self.c_lib.freedv_rawdatatx(freedv,mod_out,data) # modulate DATA and safe it into mod_out pointer     
            
        p = pyaudio.PyAudio()
        stream_tx = p.open(format=pyaudio.paInt16,
                            channels=static.AUDIO_CHANNELS,
                            rate=static.AUDIO_SAMPLE_RATE,
                            frames_per_buffer=n_nom_modem_samples,
                            output=True,
                            output_device_index=static.AUDIO_OUTPUT_DEVICE,
                            )     
        
        audio = audioop.ratecv(mod_out,2,1,static.MODEM_SAMPLE_RATE, static.AUDIO_SAMPLE_RATE, static.TX_SAMPLE_STATE)                                                   
        stream_tx.write(audio[0]) 
        
              
        print("KILL")
        stream_tx.stop_stream()
        stream_tx.close()
        p.terminate()
                        
        return mod_out

    
    # DEMODULATE DATA AND RETURN IT
    def Receive(self, mode):
        static.MODEM_RECEIVE = True
        
        
        
        self.c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
        freedv = self.c_lib.freedv_open(mode)
        #n_max_modem_samples = self.c_lib.freedv_get_n_max_modem_samples(freedv)
        bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(freedv)/8)
        

#####################################################################################################
       
        
        bytes_out = (ctypes.c_ubyte * bytes_per_frame)
        bytes_out = bytes_out() #get pointer from bytes_out
        #i = 0
        while static.MODEM_RECEIVE == True: # Listne to audio until data arrives
        
            nin = self.c_lib.freedv_nin(freedv)
            data_in = self.stream_rx.read(nin,  exception_on_overflow = False)
            
                         
            nbytes = self.c_lib.freedv_rawdatarx(freedv, bytes_out, data_in) # Demodulated data and get number of demodulated bytes
            
            if nbytes == bytes_per_frame: # make sure, we receive a full frame
                if mode >= 10:
                    
                    print("MODE: " + str(mode) + " DATA: " + str(bytes(bytes_out[:-2])))
                else:
                    print("MODE: " + str(mode) + " DATA: " + str(bytes(bytes_out)))
                    
                    
                    
                self.c_lib.freedv_set_sync(freedv, 0) #FORCE UNSYNC

                # CHECK IF FRAMETYPE CONTAINS ACK------------------------
                frametype = int.from_bytes(bytes(bytes_out[:1]), "big")      
                if 50 >= frametype >= 10 :
                    arq.data_received(bytes(bytes_out[:-2])) #send payload data to arq checker without CRC16
                
                
                # CHECK IF FRAME CONTAINS ACK------------------------
                if bytes(bytes_out[:1]) == b'\7':
                    arq.ack_received()
       
                           
                #return bytes(bytes_out[:-2])
                

        #print("KILL")
        #stream_rx.stop_stream()
        #stream_rx.close()
        #p.terminate()
