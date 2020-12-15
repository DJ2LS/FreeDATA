#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 13 13:45:58 2020

@author: DJ2LS
"""

import ctypes
from ctypes import *
import pathlib

import binascii #required for string.to_bytes() function
#import crcengine # required for CRC checksum
import sys

#sys.stdout.reconfigure(encoding='utf-8')



def main():
    
    modem = FreeDV() #Load FreeDV Class as "modem"
    
  
    data = b'TEST' #byte string which will be send
    #data = bytes(62) #byte string with XX of zeros 
    
    modulated_data = modem.Modulate(data) #Call Modulate function, which returns modulated data
    #print(modulated_data)


###################### try: / except necessary beacuse of error 32 - BrokenPipeError while piping data
    ##try:
        #print(bytes(8)) #additional zero bytes before modulated data

        #sys.stdout.buffer.write(modulated_data)    # the normal way of piping data
        #sys.stdout.flush() # flushing data
        
        #print(modulated_data, flush=True) #print modulated data with print function

    ##except (BrokenPipeError, IOError):
        ##print ('TEST BrokenPipeError caught', file = sys.stderr)
    ##sys.stderr.close()



class FreeDV():
    
    def __init__(self):

        libname = pathlib.Path().absolute() / "libcodec2.so"
        self.c_lib = ctypes.CDLL(libname) # Load FreeDV shared libary
        
        self.freedv = self.c_lib.freedv_open(12) #Set FreeDV waveform ( 10,11,12 --> DATA1-3 )
        
        self.bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(self.freedv)/8)  #get bytes per frame from selected waveform
        self.payload_per_frame = self.bytes_per_frame -2 #get frame payload because of 2byte CRC16 checksum
        
        #print(self.c_lib.freedv_get_n_nom_modem_samples(self.freedv))   


    # MODULATION-OUT OBJECT   
    def ModulationOut(self):
        #return (c_short * self.c_lib.freedv_get_n_nom_modem_samples(self.freedv))  ## all other modes
        #return (c_ubyte * self.c_lib.freedv_get_n_nom_modem_samples(self.freedv))   ## DATA modes ## Fails with n_nom_modem_samples(880) for some reason
        return (c_ubyte * 1024)   ## DATA modes another test
    # Pointer for changing buffer data type 
    def FrameBytes(self):
        return (ctypes.c_ubyte * self.bytes_per_frame)   

    # Modulate function which returns modulated data
    def Modulate(self,data_out):
        
     ##   #self.freedv_rawdatapreambletx(self.freedv, mod_out) # SEND PREAMBLE

    
    ##########################################
    
        mod_out = self.ModulationOut()() # new modulation object and get pointer to it
    
        data_list = [data_out[i:i+self.payload_per_frame] for i in range(0, len(data_out), self.payload_per_frame)] # split incomming bytes to size of 30bytes, create a list and loop through it  
        data_list_length = len(data_list)
        for i in range(data_list_length): # LOOP THROUGH DATA LIST
            #buffer = bytearray(self.bytes_per_frame) # use this if no CRC16 checksum is required
            buffer = bytearray(self.payload_per_frame) # use this if CRC16 checksum is required ( DATA1-3)
            buffer[:len(data_list[i])] = data_list[i] # set buffersize to length of data which will be send

            crc = c_ushort(self.c_lib.freedv_gen_crc16(bytes(buffer), self.payload_per_frame))     # generate CRC16
            crc = crc.value.to_bytes(2, byteorder='big') # convert buffer to 2 byte hex string
            buffer += crc        # append crc16 to buffer
        
            #print(buffer)
        
            data = self.FrameBytes().from_buffer_copy(buffer) #change data format form bytearray to ctypes.u_byte
        
            #print(len(data))
            ##return bytes(mod_out) #return modulated data as byte string

            #self.c_lib.freedv_rawdatapreambletx(self.freedv, mod_out) # SEND PREAMBLE
            #print(bytes(mod_out), flush=True)
        
          
            self.c_lib.freedv_rawdatatx(self.freedv,mod_out,data) # modulate DATA      
            print(bytes(mod_out), flush=True)





main()
