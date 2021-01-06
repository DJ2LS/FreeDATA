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
import time
import threading

import helpers
import static
import arq

#arq = arq.ARQ()



class RF():
    
    def __init__(self):
              
        #-------------------------------------------- LOAD FREEDV     
        libname = pathlib.Path().absolute() / "codec2/build_linux/src/libcodec2.so"
        self.c_lib = ctypes.CDLL(libname)

        
        
        #--------------------------------------------OPEN AUDIO CHANNEL RX
        
        self.p = pyaudio.PyAudio()
        self.stream_rx = self.p.open(format=pyaudio.paInt16, 
                            channels=static.AUDIO_CHANNELS,
                            rate=static.AUDIO_SAMPLE_RATE,
                            frames_per_buffer=static.AUDIO_FRAMES_PER_BUFFER,
                            input=True,
                            input_device_index=static.AUDIO_INPUT_DEVICE,
                            ) 

        #--------------------------------------------OPEN AUDIO CHANNEL TX

        #self.p = pyaudio.PyAudio()
        #self.stream_tx = self.p.open(format=pyaudio.paInt16,
        #                    channels=1,
        #                    rate=static.AUDIO_SAMPLE_RATE,
        #                    frames_per_buffer=2048, #n_nom_modem_samples
        #                    output=True,
        #                    output_device_index=static.AUDIO_OUTPUT_DEVICE,  #static.AUDIO_OUTPUT_DEVICE
        #                    )  
        
        
        #--------------------------------------------START AUDIO THREAD        
        
        AUDIO_LISTEN_THREAD = threading.Thread(target=self.audio_listen, name="Audio Listener")
        AUDIO_LISTEN_THREAD.start()   
        
        #--------------------------------------------START DECODER THREADS           
        
        FREEDV_700D_THREAD = threading.Thread(target=self.receive, args=[7], name="700D Decoder")
        FREEDV_700D_THREAD.start()

        FREEDV_DATAC1_THREAD = threading.Thread(target=self.receive, args=[10], name="DATAC1 Decoder")
        FREEDV_DATAC1_THREAD.start()

        FREEDV_DATAC2_THREAD = threading.Thread(target=self.receive, args=[11], name="DATAC2 Decoder")
        FREEDV_DATAC2_THREAD.start()

        FREEDV_DATAC3_THREAD = threading.Thread(target=self.receive, args=[12], name="DATAC3 Decoder")
        FREEDV_DATAC3_THREAD.start()
        
   
        #self.transmit(7,b'12345')
#--------------------------------------------------------------------------------------------------------
        
    def audio_listen(self):
        print("STARTING AUDIO LISTENER")

        while True:
            time.sleep(0.05)
            data = self.stream_rx.read(static.AUDIO_FRAMES_PER_BUFFER,  exception_on_overflow = False) 
            static.AUDIO_BUFFER += data
            #static.AUDIO_BUFFER += data.strip(b'\x00')
         
#--------------------------------------------------------------------------------------------------------
    # GET DATA AND MODULATE IT
    
    def transmit(self,mode,data_out):

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
                print("buffer for ACK: " + str(buffer))
            if mode >= 10: #generate CRC16 for modes 10-12..
                
                buffer = bytearray(payload_per_frame) # use this if CRC16 checksum is required ( DATA1-3)
                buffer[:len(data_list[i])] = data_list[i] # set buffersize to length of data which will be send

                crc = ctypes.c_ushort(self.c_lib.freedv_gen_crc16(bytes(buffer), payload_per_frame))     # generate CRC16
                crc = crc.value.to_bytes(2, byteorder='big') # convert crc to 2 byte hex string
                buffer += crc        # append crc16 to buffer
                
                
            data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
            
            self.c_lib.freedv_rawdatatx(freedv,mod_out,data) # modulate DATA and safe it into mod_out pointer     
            print(bytes(mod_out))
            
        p = pyaudio.PyAudio()
        stream_tx = p.open(format=pyaudio.paInt16,
                            channels=static.AUDIO_CHANNELS,
                            rate=static.AUDIO_SAMPLE_RATE,
                            frames_per_buffer=n_nom_modem_samples,
                            output=True,
                            output_device_index=0,  #static.AUDIO_OUTPUT_DEVICE
                            )     
        
        audio = audioop.ratecv(mod_out,2,1,static.MODEM_SAMPLE_RATE, static.AUDIO_SAMPLE_RATE, static.TX_SAMPLE_STATE)                                                   
        stream_tx.write(audio[0]) 
        
              
        print("KILL")
        stream_tx.stop_stream()
        stream_tx.close()
        p.terminate()
                        
        return mod_out

#--------------------------------------------------------------------------------------------------------    
    # DEMODULATE DATA AND RETURN IT
    def receive(self, mode):
        
        print("STARTING MODE: " + str(mode))
        
        static.MODEM_RECEIVE = True
        
        
        self.c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
        freedv = self.c_lib.freedv_open(mode)
        bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(freedv)/8)
        
        bytes_out = (ctypes.c_ubyte * bytes_per_frame)
        bytes_out = bytes_out() #get pointer from bytes_out
        
        i = 0
        while static.MODEM_RECEIVE == True: # Listne to audio until data arrives    
            time.sleep(0.05) # here we reduce CPU load
            
            nin = self.c_lib.freedv_nin(freedv)
            #data_in = self.stream_rx.read(nin,  exception_on_overflow = False)           
            #print(len(data_in))
            #nbytes = self.c_lib.freedv_rawdatarx(freedv, bytes_out, data_in) # Demodulated data and get number of demodulated bytes
            
            data_in = static.AUDIO_BUFFER
            data_in = bytes(data_in)
             
            try: 
                data_in = bytes(data_in)
                data = data_in[i:((nin*2)+i)] # * 2 because of byte size per audio frame ( 2bytes / 16bit?)
            
                self.c_lib.freedv_rawdatarx.argtype = [ctypes.POINTER(ctypes.c_ubyte), bytes_out, data] # check if really neccessary 
                nbytes = self.c_lib.freedv_rawdatarx(freedv, bytes_out, data) # demodulate audio
            
            except IndexError:
                data_in = b'\x00'
            
            
            if nbytes == bytes_per_frame: # make sure, we receive a full frame
                print("MODE: " + str(mode) + " DATA: " + str(bytes(bytes_out)))
            
                # --------------- DEBUGGING OUTPTUT -------------------------------------------
                #if mode >= 10:
                #    
                #    print("MODE: " + str(mode) + " DATA: " + str(bytes(bytes_out[:-2])))
                #    static.AUDIO_BUFFER = bytearray()
                #else:
                #    print("MODE: " + str(mode) + " DATA: " + str(bytes(bytes_out)))
                
                # --------------- END DEBUGGING OUTPTUT -------------------------------------------    
                        
                self.c_lib.freedv_set_sync(freedv, 0) #FORCE UNSYNC

                
                
                # CHECK IF FRAMETYPE IS BETWEEN 10 and 50 ------------------------
                
                frametype = int.from_bytes(bytes(bytes_out[:1]), "big")      
                if 50 >= frametype >= 10 and len(bytes_out) > 30: # --> The length check filters out random strings without CRC
                    static.AUDIO_BUFFER = bytearray()
                    print("MODE: " + str(mode) + " DATA: " + str(bytes(bytes_out[:-2])))
                    arq.data_received(bytes(bytes_out[:-2])) #send payload data to arq checker without CRC16
                else:
                    print("MODE: " + str(mode) + " DATA: " + str(bytes(bytes_out)))
                
                # CHECK IF FRAME CONTAINS ACK------------------------ --> 700D / 7 
                
                
                frametype = int.from_bytes(bytes(bytes_out[:1]), "big")
                if frametype == 60 and len(bytes_out) == 14:
                    print("ACK FRAME RECEIVED!!!!!!!!!!")
                #if bytes(bytes_out[:1]) == b'<': #b'\7':     < = 60
                    # CHECK CRC 8 OF ACK FRAME
                    
                    print(bytes_out[:1])
                    print(bytes_out[3:14])
                    
                    if bytes(bytes_out[:2]) == helpers.get_crc_8(bytes(bytes_out[3:14])):
                        print("MODE: " + str(mode) + " DATA: " + str(bytes(bytes_out)))
                        arq.ack_received()

            # ------------------ OUR NICE ITERATOR MACHINE
            if len(static.AUDIO_BUFFER) > i: # WE WILL LOOP THROUGH OUR DATA BUFFER WHILE OUR BUFFER IS BIGGER THAN THE CHUNK POSITION
                i = (nin*2) + i
            else:
                i = 0