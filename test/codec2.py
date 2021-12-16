#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ctypes
from ctypes import *
import sys
import pathlib
from enum import Enum
import numpy as np

print("loading codec2 module", file=sys.stderr)


# Enum for codec2 modes
class FREEDV_MODE(Enum):
    datac0 = 14
    datac1 = 10
    datac3 = 12
    
def FREEDV_GET_MODE(mode):
    return FREEDV_MODE[mode].value

class audio_buffer:
    # a buffer of int16 samples, using a fixed length numpy array self.buffer for storage
    # self.nbuffer is the current number of samples in the buffer
    def __init__(self, size):
        print("create audio_buffer: ", size)
        self.size = size
        self.buffer = np.zeros(size, dtype=np.int16)
        self.nbuffer = 0
    def push(self,samples):
        # add samples at the end of the buffer
        assert self.nbuffer+len(samples) <= self.size
        self.buffer[self.nbuffer:self.nbuffer+len(samples)] = samples
        self.nbuffer += len(samples)
    def pop(self,size):
        # remove samples from the start of the buffer
        self.nbuffer -= size;
        self.buffer[:self.nbuffer] = self.buffer[size:size+self.nbuffer]
        assert self.nbuffer >= 0
               
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


# resampler ---------------------------------------------------------

api.FDMDV_OS_48         = int(6)                                       # oversampling rate
api.FDMDV_OS_TAPS_48K   = int(48)                                      # number of OS filter taps at 48kHz
api.FDMDV_OS_TAPS_48_8K = int(api.FDMDV_OS_TAPS_48K/api.FDMDV_OS_48)   # number of OS filter taps at 8kHz
api.fdmdv_8_to_48_short.argtype = [c_void_p, c_void_p, c_int]
api.fdmdv_48_to_8_short.argtype = [c_void_p, c_void_p, c_int]

class resampler:
    # a buffer of int16 samples, using a fixed length numpy array self.buffer for storage
    # self.nbuffer is the current number of samples in the buffer
    MEM8 = api.FDMDV_OS_TAPS_48_8K
    MEM48 = api.FDMDV_OS_TAPS_48K
    def __init__(self, n48, n8):
        print("create 48<->8 kHz resampler with buffers of %d at 48 kHz and %d at 8 kHz" % (n48, n8))
        assert (n48 / n8) == api.FDMDV_OS_48
        self.n8 = int(n8)
        self.n48 = int(n48)
        self.in8 = np.zeros(self.MEM8 + self.n8, dtype=np.int16)
        self.out48 = np.zeros(self.n48, dtype=np.int16)
        self.in48 = np.zeros(self.MEM48 + self.n48, dtype=np.int16)
        self.out8 = np.zeros(self.n8, dtype=np.int16)
    def resample48_to_8(self,in48):
        assert in48.dtype == np.int16
        assert len(in48) == self.n48
        self.in48[self.MEM48:] = in48        
        pin48,flag = self.in48.__array_interface__['data']
        pin48 += 2*self.MEM48
        api.fdmdv_48_to_8_short(self.out8.ctypes, pin48, self.n8);
        return self.out8
    def resample8_to_48(self,in8):
        assert in8.dtype == np.int16
        assert len(in8) == self.n8
        self.in8[self.MEM8:] = in8
        pin8,flag = self.in8.__array_interface__['data']
        pin8 += 2*self.MEM8
        api.fdmdv_8_to_48_short(self.out48.ctypes, pin8, self.n8);
        return self.out48
