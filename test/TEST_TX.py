#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 13 13:45:58 2020

@author: parallels
"""

import ctypes
from ctypes import *
import pathlib


import binascii #required for string.to_bytes() function
#import codecs
import crcengine # required for CRC checksum


#import struct


import sys

#sys.stdout.reconfigure(encoding='utf-8')



def main():
    
    modem = FreeDV() #Load FreeDV Class as "modem"
    
   

    data = b'TEST' #byte string which will be send
    #data = bytes(62) #byte string with XX of zeros 
    
    modulated_data = modem.Modulate(data) #Call Modulate function, which returns modulated data
    #print(modulated_data)


###################### try: / except necessary beacuse of error 32 - BrokenPipeError while piping data
    try:
        #print(bytes(8)) #additional zero bytes before modulated data

        #sys.stdout.buffer.write(modulated_data)    # the normal way of piping data
        #sys.stdout.flush() # flushing data
        
        print(bytes(32) + modulated_data, flush=True) #print modulated data with print function

    except (BrokenPipeError, IOError):
        print ('TEST BrokenPipeError caught', file = sys.stderr)
    #sys.stderr.close()



class FreeDV():
    
    def __init__(self):

        libname = pathlib.Path().absolute() / "libcodec2.so"
        self.c_lib = ctypes.CDLL(libname) # Load FreeDV shared libary
        
        self.freedv = self.c_lib.freedv_open(12) #Set FreeDV waveform ( 10,11,12 --> DATA1-3 )
        
        self.bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(self.freedv)/8)  #get bytes per frame from selected waveform
        self.payload_per_frame = self.bytes_per_frame -2 #get frame payload because of 2byte CRC16 checksum
        
        
        ###################### CHECKSUM COMPARISON FREEDV VS CRCENGINE ########
        #https://crccalc.com
        
        teststring = b'123456789'
        

     
        # freedv crc16 checksum
        crctest2 = c_ushort(self.c_lib.freedv_gen_crc16(teststring, len(teststring)))
        print("FREEDV2: " + str(crctest2.value) + " = " + hex(crctest2.value)) #7450      
        
        
        #Python crc16 checksum
        crc_algorithm = crcengine.new('crc16-ccitt-false') #load crc16 library 
        crctest3 = crc_algorithm(teststring)
        print("CRCENGINE: " + str(crctest3) + " = " + hex(crctest3)) #8134
        
        
        #######################################################################


    # MODULATION-OUT OBJECT   
    def ModulationOut(self):
        #return (c_short * self.c_lib.freedv_get_n_nom_modem_samples(self.freedv))  ## all other modes
        return (c_ubyte * self.c_lib.freedv_get_n_nom_modem_samples(self.freedv))   ## DATA modes

    # Pointer for changing buffer data type 
    def FrameBytes(self):
        return (ctypes.c_ubyte * self.bytes_per_frame)   

    # Modulate function which returns modulated data
    def Modulate(self,data_out):
        
     ##   mod_out = self.ModulationOut()() # new modulation object and get pointer to it
     ##   #self.freedv_rawdatapreambletx(self.freedv, mod_out) # SEND PREAMBLE

    
    ##########################################
    
        mod_out = self.ModulationOut()() # new modulation object and get pointer to it
    
        #buffer = bytearray(self.bytes_per_frame) # use this if no CRC16 checksum is required
        buffer = bytearray(self.payload_per_frame) # puse this if CRC16 checksum is required ( DATA1-3)
        buffer[:len(data_out)] = data_out # set buffersize to length of data which will be send

        #buffer = self.scramble(buffer, packet_num)

        
        crc_algorithm = crcengine.new('crc16-ccitt-false') #load crc16 library 
        crc = crc_algorithm(buffer) # get new crc16 from buffer
        #print(hex(crc))
        crc = crc.to_bytes(2, byteorder='big') # convert buffer to byte string
        buffer += crc        # append crc16 to buffer
        
        #print(buffer)
        
        data = self.FrameBytes().from_buffer_copy(buffer) #change data format form bytearray to ctypes.u_byte
        
        #print(len(data))
    
       
        self.c_lib.freedv_rawdatatx(self.freedv,mod_out,data) # SEND DATA
        return bytes(mod_out) #return modulated data as byte string




main()
