#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 15 18:29:22 2020

@author: DJ2LS
"""


import ctypes
from ctypes import *
import pathlib

import binascii #required for string.to_bytes() function
import sys
import audioop

def main():
    
    modem = FreeDV() #Load FreeDV Class as "modem"
      
    #data = b'TEST' #byte string which will be send    
    
    #data = sys.stdin.read()
    #for line in sys.stdin.buffer:
    #    print(line)
    #    data = sys.stdin.buffer.read()
    #data = sys.stdin.flush()
    #data = audioop.ratecv(data,2,1,48000, 8000, None)
        #print(data)
    #    demodulated_data = modem.Demodulate(data) #Call Modulate function, which  modulates data and prints it to the terminal

    data = sys.stdin.buffer.read()
    demodulated_data = modem.Demodulate(data)


class FreeDV():
    
    def __init__(self):

        libname = pathlib.Path().absolute() / "libcodec2.so"
        self.c_lib = ctypes.CDLL(libname) # Load FreeDV shared libary
        
        self.freedv = self.c_lib.freedv_open(12) #Set FreeDV waveform ( 10,11,12 --> DATA1-3 )
        
        self.bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(self.freedv)/8)  #get bytes per frame from selected waveform
        self.payload_per_frame = self.bytes_per_frame -2 #get frame payload because of 2byte CRC16 checksum
        self.n_max_modem_samples = self.c_lib.freedv_get_n_max_modem_samples(self.freedv) 
   
    
   
    
    # MODULATION-IN OBJECT   
    def ModulationIn(self):
        return (c_short * self.n_max_modem_samples)  ##
        #return (c_short * 40000)
    
    # Pointer for changing buffer data type 
    def FrameBytes(self):
        return (c_ubyte * self.bytes_per_frame)
    # Modulate function which returns modulated data
    def Demodulate(self,data_in):
         
         buffer = bytearray(len(self.ModulationIn()())*sizeof(c_short)) # create empty byte array  
         #buffer = bytearray(40000)
         buffer[:len(data_in)] = data_in # copy across what we have
         
         modulation = self.ModulationIn() # get an empty modulation array
         modulation = modulation.from_buffer_copy(buffer) # copy buffer across and get a pointer to it.

         #print(bytes(modulation))
         bytes_out = self.FrameBytes()() # initilize a pointer to where bytes will be outputed
         #print(data_in)
         nbytes = self.c_lib.freedv_rawdatarx(self.freedv, bytes_out, data_in)
      
         nin = self.c_lib.freedv_nin(self.freedv)
         
         #print(len(modulation))
         #print(len(data_in))
         #print(len(buffer))        
         #print(self.n_max_modem_samples)

         #print(nin)

         print(self.c_lib.freedv_get_sync(self.freedv))
         if nbytes != 0:
             print(bytes(bytes_out))
        
         print(bytes(bytes_out))   
        #print(nbytes)
         #print(self.c_lib.freedv_get_total_bits_coded(self.freedv))
         #print(self.c_lib.freedv_get_total_bit_errors_coded(self.freedv))
main()         