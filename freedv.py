#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 16:58:35 2020

@author: DJ2LS
"""


import ctypes
from ctypes import *
import pathlib

import logging
import sound



class FreeDV():
    
    def __init__(self):

        libname = pathlib.Path().absolute() / "libcodec2.so"
        self.c_lib = ctypes.CDLL(libname)
        
        self.audio = sound.Audio()
        
        
        self.freedv = self.c_lib.freedv_open(3)
        self.bytes_per_frame = int(self.c_lib.freedv_get_bits_per_modem_frame(self.freedv)/8)
        self.payload_per_frame = self.bytes_per_frame -2
        
        
        logging.info("FreeDV Initialized")
        
        
    # MODULATION-OUT OBJECT   
    def ModulationOut(self):
        return (c_short * self.c_lib.freedv_get_n_nom_modem_samples(self.freedv))
 
    # MODULATION-IN OBJECT
    def ModulationIn(self):
        return (c_short * self.c_lib.freedv_get_n_nom_modem_samples(self.freedv))

    # DataFrame
    def DataFrame(self):
        return (ctypes.c_short * self.bytes_per_frame)
 
    # GET DATA AND MODULATE IT
    def Modulate(self,data_out):
        
        mod_out = self.ModulationOut()() # new modulation object and get pointer to it
        
        data = (ctypes.c_short * self.bytes_per_frame).from_buffer_copy(data_out)
        #self.freedv_rawdatapreambletx(self.freedv, mod_out) # SEND PREAMBLE
        self.c_lib.freedv_rawdatatx(self.freedv,mod_out,data) # SEND DATA
        #logging.info(bytes(mod_out))
        return mod_out

    
    # DEMODULATE DATA AND RETURN IT
    def Demodulate(self,modulation_in):
        
        mod_in = self.ModulationIn()() # new modulation object and get pointer to it
        data_in = self.DataFrame()()
        self.c_lib.freedv_rawdatarx(self.freedv, data_in, mod_in)
        
        return data_in
    
