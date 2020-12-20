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



import base64

def main():
    
    modem = FreeDV() #Load FreeDV Class as "modem"
      
    modem.Demodulate()
    #for line in sys.stdin.buffer:
    #    #print(line)
    #    modem.Demodulate(line)



class FreeDV():
    
    def __init__(self):

        libname = pathlib.Path().absolute() / "libcodec2.so"
        self.c_lib = ctypes.CDLL(libname) # Load FreeDV shared libary
        
        self.freedv = self.c_lib.freedv_open(12) #Set FreeDV waveform ( 10,11,12 --> DATA1-3 )
        
        self.bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(self.freedv)/8)  #get bytes per frame from selected waveform
        self.payload_per_frame = self.bytes_per_frame -2 #get frame payload because of 2byte CRC16 checksum
        self.n_max_modem_samples = self.c_lib.freedv_get_n_max_modem_samples(self.freedv)
        self.nin = self.c_lib.freedv_nin(self.freedv)
    
        print("N MAX MODEM SAMPLES: " + str(self.n_max_modem_samples))
        print("NIN: " + str(self.nin))
        print("BYTES PER FRAME: " + str(self.bytes_per_frame))
        
    # MODULATION-IN OBJECT   
    def ModulationIn(self):
        return (c_short * self.n_max_modem_samples)  ##
        #return (c_short * 40000)
    
    # Pointer for changing buffer data type 
    def FrameBytes(self):
        return (c_ubyte * self.bytes_per_frame)
        #return (c_ubyte * 2)
        
    # Modulate function which returns modulated data   
    def Demodulate(self):
        
        
        nin = self.c_lib.freedv_nin(self.freedv)
        
        while self.c_lib.freedv_nin(self.freedv) == nin:
            #nin = self.c_lib.freedv_nin(self.freedv)
            #print(nin)
            samples = self.c_lib.freedv_nin(self.freedv) ### MIT DER *2 funktioniert das irgendwie recht zuverlässig bei mode 5!
            print(samples)
            data_in = sys.stdin.buffer.read(samples)
            
            
         
            #buffer = bytearray(len(self.ModulationIn()())*sizeof(c_short)) # create empty byte array  
            #buffer = bytearray(len(self.ModulationIn()())*self.n_max_modem_samples) # create empty byte array 
            buffer = bytearray(1848)   # N MAX SAMPLES * 2
            print("BUFFER LENGTH: " + str(len(buffer)))
            buffer[:len(data_in)] = data_in # copy across what we have
         
            modulation = self.ModulationIn() # get an empty modulation array
            modulation = modulation.from_buffer_copy(buffer) # copy buffer across and get a pointer to it.
 
            print("MODULATION LENGTH: " + str(len(modulation)))
            bytes_out = self.FrameBytes()() # initilize a pointer to where bytes will be outputed

            nbytes = self.c_lib.freedv_rawdatarx(self.freedv, bytes_out, data_in)
      
        


            

            if nbytes > 0:
                print(bytes(bytes_out))                      
                #print(nbytes)
 











main()         
