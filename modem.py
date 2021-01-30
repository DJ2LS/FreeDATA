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

import helpers
import static
import arq

class RF():
    
    def __init__(self):  
        #-------------------------------------------- LOAD FREEDV
        libname = pathlib.Path().absolute() / "codec2/build_linux/src/libcodec2.so"
        self.c_lib = ctypes.CDLL(libname)
        #--------------------------------------------CREATE PYAUDIO  INSTANCE
        self.p = pyaudio.PyAudio()
        #--------------------------------------------GET SUPPORTED SAMPLE RATES FROM SOUND DEVICE
        #static.AUDIO_SAMPLE_RATE_RX = int(self.p.get_device_info_by_index(static.AUDIO_INPUT_DEVICE)['defaultSampleRate'])
        #static.AUDIO_SAMPLE_RATE_TX = int(self.p.get_device_info_by_index(static.AUDIO_OUTPUT_DEVICE)['defaultSampleRate'])
        static.AUDIO_SAMPLE_RATE_TX = 8000
        static.AUDIO_SAMPLE_RATE_TX = 8000
        #--------------------------------------------OPEN AUDIO CHANNEL RX
        self.stream_rx = self.p.open(format=pyaudio.paInt16, 
                            channels=static.AUDIO_CHANNELS,
                            rate=static.AUDIO_SAMPLE_RATE_RX,
                            frames_per_buffer=static.AUDIO_FRAMES_PER_BUFFER,
                            input=True,
                            input_device_index=static.AUDIO_INPUT_DEVICE,
                            ) 
        #--------------------------------------------OPEN AUDIO CHANNEL TX
        self.stream_tx = self.p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=static.AUDIO_SAMPLE_RATE_TX,
                            frames_per_buffer=static.AUDIO_FRAMES_PER_BUFFER, #n_nom_modem_samples
                            output=True,
                            output_device_index=static.AUDIO_OUTPUT_DEVICE,  #static.AUDIO_OUTPUT_DEVICE
                            )  
        #--------------------------------------------START DECODER THREAD                
        FREEDV_DECODER_THREAD = threading.Thread(target=self.receive, args=[static.FREEDV_DATA_MODE,static.FREEDV_SIGNALLING_MODE], name="FREEDV_DECODER_THREAD")
        FREEDV_DECODER_THREAD.start()  
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
        mod_out_preamble = ctypes.c_short * n_tx_modem_samples #1760 for mode 10,11,12 #4000 for mode 9
        mod_out_preamble = mod_out_preamble()
                
        data_list = [data_out[i:i+payload_per_frame] for i in range(0, len(data_out), payload_per_frame)] # split incomming bytes to size of 30bytes, create a list and loop through it  
        data_list_length = len(data_list)
        for i in range(data_list_length): # LOOP THROUGH DATA LIST

            buffer = bytearray(payload_per_frame) # use this if CRC16 checksum is required ( DATA1-3)
            buffer[:len(data_list[i])] = data_list[i] # set buffersize to length of data which will be send

            crc = ctypes.c_ushort(self.c_lib.freedv_gen_crc16(bytes(buffer), payload_per_frame))     # generate CRC16
            crc = crc.value.to_bytes(2, byteorder='big') # convert crc to 2 byte hex string
            buffer += crc        # append crc16 to buffer
     
            data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
            self.c_lib.freedv_rawdatapreambletx(freedv, mod_out_preamble)
            self.c_lib.freedv_rawdatatx(freedv,mod_out,data) # modulate DATA and safe it into mod_out pointer     

            # -------------- preamble area
            # WE NEED TO ADJUST IT FOR SINGLE TRANSMISSION

            txbuffer = bytearray()    
            txbuffer += bytes(mod_out_preamble)
            txbuffer += bytes(mod_out)
            #txbuffer = txbuffer.rstrip(b'\x00')
            # -------------- audio sample rate conversion
            
            # -------------- transmit audio
            self.stream_tx.write(bytes(txbuffer)) 

#--------------------------------------------------------------------------------------------------------     
    def transmit_arq_ack(self,ack_buffer):
    
        static.ARQ_STATE = 'SENDING_ACK'
    
        self.c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
        freedv = self.c_lib.freedv_open(static.FREEDV_SIGNALLING_MODE)
        bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(freedv)/8)
        payload_per_frame = bytes_per_frame -2
        n_nom_modem_samples = self.c_lib.freedv_get_n_nom_modem_samples(freedv)
        n_tx_modem_samples = self.c_lib.freedv_get_n_tx_modem_samples(freedv)*2 #get n_tx_modem_samples which defines the size of the modulation object
          
        mod_out = ctypes.c_short * n_tx_modem_samples
        mod_out = mod_out()
        mod_out_preamble = ctypes.c_short * (n_tx_modem_samples*2) #1760 for mode 10,11,12 #4000 for mode 9
        mod_out_preamble = mod_out_preamble()

        buffer = bytearray(payload_per_frame) # use this if CRC16 checksum is required ( DATA1-3)
        buffer[:len(ack_buffer)] = ack_buffer # set buffersize to length of data which will be send

        crc = ctypes.c_ushort(self.c_lib.freedv_gen_crc16(bytes(buffer), payload_per_frame))     # generate CRC16
        crc = crc.value.to_bytes(2, byteorder='big') # convert crc to 2 byte hex string
        buffer += crc        # append crc16 to buffer
        print(bytes(buffer))
        data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
        
        self.c_lib.freedv_rawdatapreambletx(freedv, mod_out_preamble)
        self.c_lib.freedv_rawdatatx(freedv,mod_out,data) # modulate DATA and safe it into mod_out pointer     

        txbuffer = bytearray()    
        txbuffer += bytes(mod_out_preamble)
        txbuffer += bytes(mod_out)
        txbuffer = txbuffer.rstrip(b'\x00')
        
            # -------------- transmit audio twice
        self.stream_tx.write(bytes(txbuffer))
       
        static.ARQ_STATE = 'RECEIVING_DATA'
#--------------------------------------------------------------------------------------------------------     
   # GET ARQ BURST FRAME VOM BUFFER AND MODULATE IT 
    def transmit_arq_burst(self):
        static.ARQ_STATE = 'SENDING_DATA'
       
        
        self.c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
        freedv = self.c_lib.freedv_open(static.FREEDV_DATA_MODE)
        static.FREEDV_DATA_BYTES_PER_FRAME = int(self.c_lib.freedv_get_bits_per_modem_frame(freedv)/8)
        static.FREEDV_DATA_PAYLOAD_PER_FRAME = static.FREEDV_DATA_BYTES_PER_FRAME -2
        
        print(static.FREEDV_DATA_BYTES_PER_FRAME)
        
        n_nom_modem_samples = self.c_lib.freedv_get_n_nom_modem_samples(freedv)
        n_tx_modem_samples = self.c_lib.freedv_get_n_tx_modem_samples(freedv)*2 #get n_tx_modem_samples which defines the size of the modulation object
          
        mod_out = ctypes.c_short * n_tx_modem_samples
        mod_out = mod_out()
        mod_out_preamble = ctypes.c_short * (1760*2) #1760 for mode 10,11,12 #4000 for mode 9
        mod_out_preamble = mod_out_preamble()

        self.c_lib.freedv_rawdatapreambletx(freedv, mod_out_preamble);
        txbuffer = bytearray()
        txbuffer += bytes(mod_out_preamble)
        
        time_start = time.time()
        for n in range(0,static.ARQ_TX_N_FRAMES_PER_BURST):

            #---------------------------BUILD ARQ BURST ---------------------------------------------------------------------
            frame_type = 10 + static.ARQ_TX_N_FRAMES_PER_BURST
            frame_type = bytes([frame_type])
            print(frame_type)
            print("static.ARQ_N_SENT_FRAMES: " + str(static.ARQ_N_SENT_FRAMES))
            print("static.ARQ_TX_N_FRAMES_PER_BURST: " + str(static.ARQ_TX_N_FRAMES_PER_BURST))
            
            payload_data = bytes(static.TX_BUFFER[static.ARQ_N_SENT_FRAMES + n])
                    
            arqframe = frame_type + static.ARQ_BURST_PAYLOAD_CRC + payload_data
                    
            buffer = bytearray(static.FREEDV_DATA_PAYLOAD_PER_FRAME) # create TX buffer 
            buffer[:len(arqframe)] = arqframe # set buffersize to length of data which will be send
                                
            crc = ctypes.c_ushort(self.c_lib.freedv_gen_crc16(bytes(buffer), static.FREEDV_DATA_PAYLOAD_PER_FRAME))     # generate CRC16
            crc = crc.value.to_bytes(2, byteorder='big') # convert crc to 2 byte hex string
            buffer += crc        # append crc16 to buffer

            data = (ctypes.c_ubyte * static.FREEDV_DATA_BYTES_PER_FRAME).from_buffer_copy(buffer)
            self.c_lib.freedv_rawdatatx(freedv,mod_out,data) # modulate DATA and safe it into mod_out pointer 
            txbuffer += bytes(mod_out)

            # -------------- transmit audio
        self.stream_tx.write(bytes(txbuffer)) 

        static.ARQ_STATE = 'RECEIVING_ACK'
        
#--------------------------------------------------------------------------------------------------------         
    def receive(self,data_mode,signalling_mode):
    
        print("RECEIVING FOR DATA MODE: " + str(data_mode))
        print("RECEIVING FOR SIGNALLING MODE: " + str(signalling_mode))
    
        self.c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
        
        freedv_data = self.c_lib.freedv_open(data_mode)
        freedv_signalling = self.c_lib.freedv_open(signalling_mode)      

        static.FREEDV_DATA_BYTES_PER_FRAME = int(self.c_lib.freedv_get_bits_per_modem_frame(freedv_data)/8)
        static.FREEDV_DATA_PAYLOAD_PER_FRAME = static.FREEDV_DATA_BYTES_PER_FRAME -2
        static.FREEDV_SIGNALLING_BYTES_PER_FRAME = int(self.c_lib.freedv_get_bits_per_modem_frame(freedv_signalling)/8)
        static.FREEDV_SIGNALLING_PAYLOAD_PER_FRAME = static.FREEDV_SIGNALLING_BYTES_PER_FRAME -2
  
        data_bytes_out = (ctypes.c_ubyte * static.FREEDV_DATA_BYTES_PER_FRAME)
        data_bytes_out = data_bytes_out() #get pointer from bytes_out    

        signalling_bytes_out = (ctypes.c_ubyte * static.FREEDV_SIGNALLING_BYTES_PER_FRAME)
        signalling_bytes_out = signalling_bytes_out() #get pointer from bytes_out 

                
        while 1:
            time.sleep(0.01)
            
            while static.ARQ_STATE == 'RECEIVING_DATA':
                time.sleep(0.01)
                
                nin = self.c_lib.freedv_nin(freedv_data)
                nin = int(nin*(static.AUDIO_SAMPLE_RATE_RX/static.MODEM_SAMPLE_RATE))

                data_in = self.stream_rx.read(nin,  exception_on_overflow = False)  
                data_in = audioop.ratecv(data_in,2,1,static.AUDIO_SAMPLE_RATE_RX, static.MODEM_SAMPLE_RATE, None) 
                data_in = data_in[0].rstrip(b'\x00')
                
                #print(data_in)
                
                self.c_lib.freedv_rawdatarx.argtype = [ctypes.POINTER(ctypes.c_ubyte), data_bytes_out, data_in] # check if really neccessary 
                nbytes = self.c_lib.freedv_rawdatarx(freedv_data, data_bytes_out, data_in) # demodulate audio
                print(self.c_lib.freedv_get_rx_status(freedv_data))
                
                #modem_stats_snr = c_float()
                #modem_stats_sync = c_int()
                
                #self.c_lib.freedv_get_modem_stats(freedv_data,byref(modem_stats_sync), byref(modem_stats_snr))
                #modem_stats_snr = modem_stats_snr.value
                #print(modem_stats_snr)               
 


                if nbytes == static.FREEDV_DATA_BYTES_PER_FRAME:
                                              
                    # CHECK IF FRAMETYPE IS BETWEEN 10 and 50 ------------------------
                    frametype = int.from_bytes(bytes(data_bytes_out[:1]), "big")      
                    if 50 >= frametype >= 10 and len(data_bytes_out) > 30: # --> The length check filters out random strings without CRC
                        print("MODE: " + str(data_mode) + " DATA: " + str(bytes(data_bytes_out[:-2])))
                        arq.data_received(bytes(data_bytes_out[:-2])) #send payload data to arq checker without CRC16
                        
                        
                        #self.c_lib.freedv_set_sync(freedv_data, 0) #FORCE UNSYNC
                    else:
                        print("MODE: " + str(data_mode) + " DATA: " + str(bytes(data_bytes_out)))
                
                
                
                # NEEDS TO BE OPTIMIZED
                # DO UNSYNC IF LAST FRAME PER BURST SENT
                if len(static.ARQ_RX_BURST_BUFFER) == static.ARQ_N_RX_FRAMES_PER_BURSTS and len(static.ARQ_RX_BURST_BUFFER) != 0:
                    print("DOING UNSYNC")
                    self.c_lib.freedv_set_sync(freedv_data, 0) #FORCE UNSYNC

                

            while static.ARQ_STATE == 'IDLE' or static.ARQ_STATE == 'RECEIVING_ACK':
                time.sleep(0.01)

                nin = self.c_lib.freedv_nin(freedv_signalling)
                nin = int(nin*(static.AUDIO_SAMPLE_RATE_RX/static.MODEM_SAMPLE_RATE))

                data_in = self.stream_rx.read(nin,  exception_on_overflow = False)  
                data_in = audioop.ratecv(data_in,2,1,static.AUDIO_SAMPLE_RATE_RX, static.MODEM_SAMPLE_RATE, None) 
                data_in = data_in[0].rstrip(b'\x00')
                
                self.c_lib.freedv_rawdatarx.argtype = [ctypes.POINTER(ctypes.c_ubyte), signalling_bytes_out, data_in] # check if really neccessary 
                nbytes = self.c_lib.freedv_rawdatarx(freedv_signalling, signalling_bytes_out, data_in) # demodulate audio
                
                
                    # CHECK IF FRAME CONTAINS ACK------------------------ --> 700D / 7 
                 
                frametype = int.from_bytes(bytes(signalling_bytes_out[:1]), "big")
                if frametype == 60 and len(signalling_bytes_out) == static.FREEDV_SIGNALLING_BYTES_PER_FRAME:
                       arq.ack_received()
                       # print("ACK FRAME RECEIVED!!!!!!!!!!")
                    #if bytes(bytes_out[:1]) == b'<': #b'\7':     < = 60
                        # CHECK CRC 8 OF ACK FRAME
                    
                       # print(signalling_bytes_out[:1])
                       # print(signalling_bytes_out[3:14])
                    
                       # if bytes(signalling_bytes_out[:2]) == helpers.get_crc_8(bytes(signalling_bytes_out[3:14])):
                       #     print("MODE: " + str(signalling_mode) + " DATA: " + str(bytes(signalling_bytes_out)))
                       #     arq.ack_received()


