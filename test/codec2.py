#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ctypes
from ctypes import *
import sys
import pathlib
from enum import Enum

print("loading codec2 module", file=sys.stderr)


# Enum for codec2 modes
class FREEDV_MODE(Enum):
    datac0 = 14
    datac1 = 10
    datac3 = 12
    
def FREEDV_GET_MODE(mode):
    return FREEDV_MODE[mode].value



# LOAD FREEDV
libname = "libcodec2.so"
api = ctypes.CDLL(libname)


# ctypes function init        

api.freedv_open.argype = [c_int]
api.freedv_open.restype = c_void_p

api.freedv_get_bits_per_modem_frame.argtype = [c_void_p]
api.freedv_get_bits_per_modem_frame.restype = c_int

api.freedv_nin.argtype = [c_void_p]
api.freedv_nin.restype = c_int

api.freedv_rawdatarx.argtype = [c_void_p, c_char_p, c_char_p]
api.freedv_rawdatarx.restype = c_int

api.freedv_rawdatatx.argtype = [c_void_p, c_char_p, c_char_p]
api.freedv_rawdatatx.restype = c_int

api.freedv_rawdatapostambletx.argtype = [c_void_p, c_char_p, c_char_p]
api.freedv_rawdatapostambletx.restype = c_int

api.freedv_rawdatapreambletx.argtype = [c_void_p, c_char_p, c_char_p]
api.freedv_rawdatapreambletx.restype = c_int

api.freedv_get_n_max_modem_samples.argtype = [c_void_p]
api.freedv_get_n_max_modem_samples.restype = c_int

api.freedv_set_frames_per_burst.argtype = [c_void_p, c_int]
api.freedv_set_frames_per_burst.restype = c_void_p
      
api.freedv_get_rx_status.argtype = [c_void_p]
api.freedv_get_rx_status.restype = c_int  

api.freedv_get_modem_stats.argtype = [c_void_p, c_void_p, c_void_p]
api.freedv_get_modem_stats.restype = c_int

api.freedv_get_n_tx_postamble_modem_samples.argtype = [c_void_p]
api.freedv_get_n_tx_postamble_modem_samples.restype = c_int 

api.freedv_get_n_tx_preamble_modem_samples.argtype = [c_void_p]
api.freedv_get_n_tx_preamble_modem_samples.restype = c_int 

api.freedv_get_n_tx_modem_samples.argtype = [c_void_p]
api.freedv_get_n_tx_modem_samples.restype = c_int 


api.FREEDV_FS_8000 = 8000
api.FREEDV_MODE_DATAC1 = 10
api.FREEDV_MODE_DATAC3 = 12
api.FREEDV_MODE_DATAC0 = 14




    
    

