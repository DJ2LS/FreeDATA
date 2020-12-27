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
        
    
        self.p = pyaudio.PyAudio()
        self.defaultFrames = static.DEFAULT_FRAMES
        self.audio_input_device = static.AUDIO_INPUT_DEVICE
        self.audio_output_device = static.AUDIO_OUTPUT_DEVICE 
        self.tx_sample_state = static.TX_SAMPLE_STATE
        self.rx_sample_state = static.RX_SAMPLE_STATE
        self.audio_sample_rate = static.AUDIO_SAMPLE_RATE
        self.modem_sample_rate = static.MODEM_SAMPLE_RATE
        self.audio_frames_per_buffer = static.AUDIO_FRAMES_PER_BUFFER
        self.audio_channels = static.AUDIO_CHANNELS
        self.format = pyaudio.paInt16
        self.stream = None
        
        
        #self.data_input = "stdin"
        self.data_input = "audio"
        #self.data_output = "stdout"
        self.data_output = "audio"
        
        
        libname = pathlib.Path().absolute() / "codec2/build_linux/src/libcodec2.so"
        self.c_lib = ctypes.CDLL(libname)
        
        
        self.mode = static.FREEDV_MODE # define mode
        
        
        self.freedv = self.c_lib.freedv_open(self.mode)
        self.bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(self.freedv)/8)
        self.payload_per_frame = self.bytes_per_frame -2        
        self.n_tx_modem_samples = self.c_lib.freedv_get_n_tx_modem_samples(self.freedv)*2 #get n_tx_modem_samples which defines the size of the modulation object
        self.n_max_modem_samples = self.c_lib.freedv_get_n_max_modem_samples(self.freedv)
        self.n_nom_modem_samples = self.c_lib.freedv_get_n_nom_modem_samples(self.freedv)
        self.nin = self.c_lib.freedv_nin(self.freedv)

        static.FREEDV_BYTES_PER_FRAME = self.bytes_per_frame
        static.FREEDV_PAYLOAD_PER_FRAME = self.payload_per_frame

        
    # MODULATION-OUT OBJECT   
    def ModulationOut(self):
        return (c_short * self.n_tx_modem_samples)
 
    # MODULATION-IN OBJECT
    def ModulationIn(self):
        return (c_short * (self.n_max_modem_samples))

    # FRAME BYTES
    # Pointer for changing buffer data type 
    def FrameBytes(self):
        return (c_ubyte * self.bytes_per_frame)
 
    # GET DATA AND MODULATE IT
    
    def Transmit(self,data_out):
                  
        mod_out = self.ModulationOut()() # new modulation object and get pointer to it
        
    
        data_list = [data_out[i:i+self.payload_per_frame] for i in range(0, len(data_out), self.payload_per_frame)] # split incomming bytes to size of 30bytes, create a list and loop through it  
        data_list_length = len(data_list)
        for i in range(data_list_length): # LOOP THROUGH DATA LIST
            
            if self.mode < 10: # don't generate CRC16 for modes 0 - 9
            
                buffer = bytearray(self.bytes_per_frame) # use this if no CRC16 checksum is required
                buffer[:len(data_list[i])] = data_list[i] # set buffersize to length of data which will be send
                
            if self.mode >= 10: #generate CRC16 for modes 10-12..
                
                buffer = bytearray(self.payload_per_frame) # use this if CRC16 checksum is required ( DATA1-3)
                buffer[:len(data_list[i])] = data_list[i] # set buffersize to length of data which will be send

                crc = c_ushort(self.c_lib.freedv_gen_crc16(bytes(buffer), self.payload_per_frame))     # generate CRC16
                crc = crc.value.to_bytes(2, byteorder='big') # convert crc to 2 byte hex string
                buffer += crc        # append crc16 to buffer
                
                
            data = self.FrameBytes().from_buffer_copy(buffer) #change data format from bytearray to ctypes.u_byte and copy from buffer to data
     
            self.c_lib.freedv_rawdatatx(self.freedv,mod_out,data) # modulate DATA and safe it into mod_out pointer     
            
        if self.data_output == "stdout":
            sys.stdout.buffer.write(mod_out)    # print data to terminal for piping the output to other programs
            sys.stdout.flush() # flushing stdout
                     
        if self.data_output == "audio":
            #print(self.audio_channels)
            stream_tx = self.p.open(format=self.format, 
                            channels=self.audio_channels,
                            rate=self.audio_sample_rate,
                            frames_per_buffer=self.n_nom_modem_samples,
                            output=True,
                            output_device_index=self.audio_output_device,
                            )     
        
            audio = audioop.ratecv(mod_out,2,1,self.modem_sample_rate, self.audio_sample_rate, self.tx_sample_state)                                                   
            stream_tx.write(audio[0])       
            stream_tx.close()
                        
        return mod_out

    
    # DEMODULATE DATA AND RETURN IT
    def Receive(self):

        # Open Audio Channel once
        stream_rx = self.p.open(format=self.format, 
                            channels=self.audio_channels,
                            rate=self.audio_sample_rate,
                            frames_per_buffer=self.n_max_modem_samples,
                            input=True,
                            input_device_index=self.audio_input_device,
                            ) 
        
        
        while static.MODEM_RECEIVE == True: # Listne to audio until data arrives
        
        
            #if self.data_input == "stdin":
            #    samples = self.c_lib.freedv_nin(self.freedv)*2 ### MIT DER *2 funktioniert das irgendwie recht zuverlässig bei mode 5! Bei Mode 12 auch
            #    data_in = sys.stdin.buffer.read(samples)
            if self.data_input == "audio":
                
                data_in = stream_rx.read(self.c_lib.freedv_nin(self.freedv),  exception_on_overflow = False)
                #print(bytes(data_in))
            buffer = bytearray(self.n_max_modem_samples*2) # N MAX SAMPLES * 2
            buffer[:len(data_in)] = data_in # copy across what we have
            
            
            self.ModulationIn()() #Create new ModulationIn Object
            modulation = self.ModulationIn()# get an empty modulation array
            modulation = modulation.from_buffer_copy(buffer) # copy buffer across and get a pointer to it.
            
            bytes_out = self.FrameBytes()() # initilize a pointer to where bytes will be outputed
            
            nbytes = self.c_lib.freedv_rawdatarx(self.freedv, bytes_out, data_in) # Demodulated data and get number of demodulated bytes

            if nbytes == self.bytes_per_frame: # make sure, we receive a full frame
            
            
                print(bytes(bytes_out[:-2]))
                self.c_lib.freedv_set_sync(self.freedv, 0)



                # CHECK IF FRAMETYPE CONTAINS ACK------------------------
                frametype = int.from_bytes(bytes(bytes_out[:1]), "big")      
                if 20 >= frametype >= 10 :
                    arq.receive(bytes(bytes_out))
                
                # CHECK IF FRAME CONTAINS ACK------------------------
                #if bytes(bytes_out[:6]) == b'REQACK':
           
                    #logging.info("RX | ACK REQUESTED!")         
                    #time.sleep(5)
                    #logging.info("TX | SENDING ACK FRAME")
                    #self.Transmit(b'ACK')
                #----------------------------------------------------

                # CHECK IF FRAME CONTAINS ACK------------------------
                if bytes(bytes_out[:3]) == b'ACK':
               
                    logging.info("TX | ACK RCVD!")
                    static.ACK_TIMEOUT = 1 #Force timer to stop waiting
                    static.ACK_RECEIVED = 1 #Force data loops of TNC to stop and continue with next frame
                    
                #----------------------------------------------------
                           
                #return bytes(bytes_out[:-2])
                

         

