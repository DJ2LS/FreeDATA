#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ctypes
from ctypes import *
import sys
import os
#import pathlib
from enum import Enum
import numpy as np
#print("loading codec2 module", file=sys.stderr)
from threading import Lock

# Enum for codec2 modes
class FREEDV_MODE(Enum):
    datac0 = 14
    datac1 = 10
    datac3 = 12
    
def freedv_get_mode(mode):
    return FREEDV_MODE[mode].value


# check if we are running in a pyinstaller environment
try:
    app_path = sys._MEIPASS
except:
    app_path = os.path.abspath(".")
sys.path.append(app_path)

# -------------------------------------------- LOAD FREEDV
# codec2 search pathes in descending order
# libcodec2.so                                                          ctests
# pathlib.Path("codec2/build_linux/src/libcodec2.so.1.0")               manual build
# pathlib.Path("lib/codec2/linux/libcodec2.so.1.0")                     precompiled
# pathlib.Path("../../tnc/codec2/build_linux/src/libcodec2.so.1.0")     external loading manual build
# pathlib.Path("../../tnc/lib/codec2/linux/libcodec2.so.1.0")           external loading precompiled

if sys.platform == 'linux':
    libname = ["libcodec2.so", \
                os.path.join(app_path, "codec2/build_linux/src/libcodec2.so.1.0"), \
                os.path.join(app_path, "lib/codec2/linux/libcodec2.so.1.0"), \
                os.path.join(app_path, "../tnc/codec2/build_linux/src/libcodec2.so.1.0"), \
                os.path.join(app_path, "../tnc/lib/codec2/linux/libcodec2.so.1.0"), \
                ]
elif sys.platform == 'win32' or sys.platform == 'win64':
    libname = ["libcodec2.dll", \
                os.path.join(base_path, "lib\\codec2\\windows\\libcodec2.dll")
                ]
else:
    print(f"[C2 ] Platform not supported {sys.platform}", file=sys.stderr)  
    
# iterate through codec2 search pathes
for i in libname:
    try:
        api = ctypes.CDLL(i)
        print(f"[C2 ] Codec2 library found - {i}", file=sys.stderr)
        break
    except:
        print(f"[C2 ] Codec2 library not found - {i}", file=sys.stderr)
        pass
# quit module if codec2 cant be loaded    
if not 'api' in locals():
    print(f"[C2 ] Loading Codec2 library failed", file=sys.stderr)




    
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

api.freedv_get_n_max_modem_samples.argtype = [c_void_p]
api.freedv_get_n_max_modem_samples.restype = c_int 

api.FREEDV_FS_8000 = 8000
api.FREEDV_MODE_DATAC1 = 10
api.FREEDV_MODE_DATAC3 = 12
api.FREEDV_MODE_DATAC0 = 14

# Return code flags for freedv_get_rx_status() function
api.FREEDV_RX_TRIAL_SYNC = 0x1       # demodulator has trial sync
api.FREEDV_RX_SYNC       = 0x2       # demodulator has sync
api.FREEDV_RX_BITS       = 0x4       # data bits have been returned
api.FREEDV_RX_BIT_ERRORS = 0x8       # FEC may not have corrected all bit errors (not all parity checks OK)

api.rx_sync_flags_to_text = [
    "----",
    "---T",
    "--S-",
    "--ST",
    "-B--",
    "-B-T",
    "-BS-",
    "-BST",
    "E---",
    "E--T",
    "E-S-",
    "E-ST",
    "EB--",
    "EB-T",
    "EBS-",
    "EBST"]

# audio buffer ---------------------------------------------------------

class audio_buffer:
    # a buffer of int16 samples, using a fixed length numpy array self.buffer for storage
    # self.nbuffer is the current number of samples in the buffer
    def __init__(self, size):
        print("create audio_buffer: ", size)
        self.size = size
        self.buffer = np.zeros(size, dtype=np.int16)
        self.nbuffer = 0
        self.mutex = Lock()
    def push(self,samples):
        self.mutex.acquire()
        # add samples at the end of the buffer
        assert self.nbuffer+len(samples) <= self.size
        self.buffer[self.nbuffer:self.nbuffer+len(samples)] = samples
        self.nbuffer += len(samples)
        self.mutex.release()
    def pop(self,size):
        self.mutex.acquire()
        # remove samples from the start of the buffer
        self.nbuffer -= size;
        self.buffer[:self.nbuffer] = self.buffer[size:size+self.nbuffer]
        assert self.nbuffer >= 0
        self.mutex.release()
        
# resampler ---------------------------------------------------------

api.FDMDV_OS_48         = int(6)                                       # oversampling rate
api.FDMDV_OS_TAPS_48K   = int(48)                                      # number of OS filter taps at 48kHz
api.FDMDV_OS_TAPS_48_8K = int(api.FDMDV_OS_TAPS_48K/api.FDMDV_OS_48)   # number of OS filter taps at 8kHz
api.fdmdv_8_to_48_short.argtype = [c_void_p, c_void_p, c_int]
api.fdmdv_48_to_8_short.argtype = [c_void_p, c_void_p, c_int]

class resampler:
    # resample an array of variable length, we just store the filter memories here
    MEM8 = api.FDMDV_OS_TAPS_48_8K
    MEM48 = api.FDMDV_OS_TAPS_48K

    def __init__(self):
        print("create 48<->8 kHz resampler")
        self.filter_mem8 = np.zeros(self.MEM8, dtype=np.int16)
        self.filter_mem48 = np.zeros(self.MEM48)
        
        
    def resample48_to_8(self,in48):
        assert in48.dtype == np.int16
        # length of input vector must be an integer multiple of api.FDMDV_OS_48
        assert(len(in48) % api.FDMDV_OS_48 == 0)

        # concat filter memory and input samples
        in48_mem = np.zeros(self.MEM48+len(in48), dtype=np.int16)
        in48_mem[:self.MEM48] = self.filter_mem48
        in48_mem[self.MEM48:] = in48

        # In C: pin48=&in48_mem[MEM48]
        pin48 = byref(np.ctypeslib.as_ctypes(in48_mem), 2*self.MEM48)
        n8 = int(len(in48) / api.FDMDV_OS_48)
        out8 = np.zeros(n8, dtype=np.int16)
        api.fdmdv_48_to_8_short(out8.ctypes, pin48, n8);

        # store memory for next time
        self.filter_mem48 = in48_mem[:self.MEM48]

        return out8

    def resample8_to_48(self,in8):
        assert in8.dtype == np.int16

        # concat filter memory and input samples
        in8_mem = np.zeros(self.MEM8+len(in8), dtype=np.int16)
        in8_mem[:self.MEM8] = self.filter_mem8
        in8_mem[self.MEM8:] = in8

        # In C: pin8=&in8_mem[MEM8]
        pin8 = byref(np.ctypeslib.as_ctypes(in8_mem), 2*self.MEM8)
        out48 = np.zeros(api.FDMDV_OS_48*len(in8), dtype=np.int16)
        api.fdmdv_8_to_48_short(out48.ctypes, pin8, len(in8));

        # store memory for next time
        self.filter_mem8 = in8_mem[:self.MEM8]

        return out48
