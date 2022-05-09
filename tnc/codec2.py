#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import ctypes
from ctypes import *
import sys
import os
from enum import Enum
import numpy as np
from threading import Lock
import glob
import structlog


# Enum for codec2 modes
class FREEDV_MODE(Enum):
    """
    enum for codec2 modes and names
    """
    fsk_ldpc_0 = 200
    fsk_ldpc_1 = 201
    fsk_ldpc = 9
    datac0 = 14
    datac1 = 10
    datac3 = 12
    allmodes = 255

# function for returning the mode value
def freedv_get_mode_value_by_name(mode):
    """
    get the codec2 mode by entering its string
    Args:
      mode:

    Returns: int

    """
    return FREEDV_MODE[mode].value

# function for returning the mode name
def freedv_get_mode_name_by_value(mode):
    """
    get the codec2 mode name as string
    Args:
      mode:

    Returns: string

    """
    return FREEDV_MODE(mode).name


# check if we are running in a pyinstaller environment
try:
    app_path = sys._MEIPASS
except:
    app_path = os.path.abspath(".")
sys.path.append(app_path)

structlog.get_logger("structlog").info("[C2 ] Searching for libcodec2...")
if sys.platform == 'linux':
    files = glob.glob('**/*libcodec2*',recursive=True)
    files.append('libcodec2.so')
elif sys.platform == 'darwin':
    files = glob.glob('**/*libcodec2*.dylib',recursive=True)
elif sys.platform == 'win32' or sys.platform == 'win64':
    files = glob.glob('**\*libcodec2*.dll',recursive=True)
else:
    files = []

for file in files:
    try:
        api = ctypes.CDLL(file)
        structlog.get_logger("structlog").info("[C2 ] Libcodec2 loaded", path=file)
        break
    except Exception as e:
        structlog.get_logger("structlog").warning("[C2 ] Libcodec2 found but not loaded", path=file, e=e)

# quit module if codec2 cant be loaded
if not 'api' in locals():
    structlog.get_logger("structlog").critical("[C2 ] Libcodec2 not loaded", path=file)
    os._exit(1)

# ctypes function init

#api.freedv_set_tuning_range.restype = c_int
#api.freedv_set_tuning_range.argype = [c_void_p, c_float, c_float]

api.freedv_open.argype = [c_int]
api.freedv_open.restype = c_void_p

api.freedv_open_advanced.argtype = [c_int, c_void_p]
api.freedv_open_advanced.restype = c_void_p

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
api.FREEDV_MODE_FSK_LDPC = 9

# -------------------------------- FSK LDPC MODE SETTINGS

# advanced structure for fsk modes
class ADVANCED(ctypes.Structure):
    """ """
    _fields_ = [
        ("interleave_frames", ctypes.c_int),
        ("M", ctypes.c_int),
        ("Rs", ctypes.c_int),
        ("Fs", ctypes.c_int),
        ("first_tone", ctypes.c_int),
        ("tone_spacing", ctypes.c_int),
        ("codename", ctypes.c_char_p),
    ]

'''
adv.interleave_frames = 0                       # max amplitude
adv.M = 2                                       # number of fsk tones 2/4
adv.Rs = 100                                    # symbol rate
adv.Fs = 8000                                   # sample rate
adv.first_tone = 1500                           # first tone freq
adv.tone_spacing = 200                          # shift between tones
adv.codename = 'H_128_256_5'.encode('utf-8')    # code word

HRA_112_112          rate 0.50 (224,112)    BPF: 14     not working
HRA_56_56            rate 0.50 (112,56)     BPF: 7      not working
H_2064_516_sparse    rate 0.80 (2580,2064)  BPF: 258    working
HRAb_396_504         rate 0.79 (504,396)    BPF: 49     not working
H_256_768_22         rate 0.33 (768,256)    BPF: 32     working
H_256_512_4          rate 0.50 (512,256)    BPF: 32     working
HRAa_1536_512        rate 0.75 (2048,1536)  BPF: 192    not working
H_128_256_5          rate 0.50 (256,128)    BPF: 16     working
H_4096_8192_3d       rate 0.50 (8192,4096)  BPF: 512    not working
H_16200_9720         rate 0.60 (16200,9720) BPF: 1215   not working
H_1024_2048_4f       rate 0.50 (2048,1024)  BPF: 128    working
'''
# --------------- 2 FSK H_128_256_5, 16 bytes
api.FREEDV_MODE_FSK_LDPC_0_ADV = ADVANCED()
api.FREEDV_MODE_FSK_LDPC_0_ADV.interleave_frames = 0
api.FREEDV_MODE_FSK_LDPC_0_ADV.M = 4
api.FREEDV_MODE_FSK_LDPC_0_ADV.Rs = 100
api.FREEDV_MODE_FSK_LDPC_0_ADV.Fs = 8000
api.FREEDV_MODE_FSK_LDPC_0_ADV.first_tone = 1400 # 1150 4fsk, 1500 2fsk
api.FREEDV_MODE_FSK_LDPC_0_ADV.tone_spacing = 120 #200
api.FREEDV_MODE_FSK_LDPC_0_ADV.codename = 'H_128_256_5'.encode('utf-8')   # code word

# --------------- 4 H_256_512_4, 7 bytes
api.FREEDV_MODE_FSK_LDPC_1_ADV = ADVANCED()
api.FREEDV_MODE_FSK_LDPC_1_ADV.interleave_frames = 0
api.FREEDV_MODE_FSK_LDPC_1_ADV.M = 4
api.FREEDV_MODE_FSK_LDPC_1_ADV.Rs = 100
api.FREEDV_MODE_FSK_LDPC_1_ADV.Fs = 8000
api.FREEDV_MODE_FSK_LDPC_1_ADV.first_tone = 1250 # 1250 4fsk, 1500 2fsk
api.FREEDV_MODE_FSK_LDPC_1_ADV.tone_spacing = 200
api.FREEDV_MODE_FSK_LDPC_1_ADV.codename = 'H_256_512_4'.encode('utf-8')   # code word

# ------- MODEM STATS STRUCTURES

MODEM_STATS_NC_MAX =       50+1
MODEM_STATS_NR_MAX =       160
MODEM_STATS_ET_MAX =       8
MODEM_STATS_EYE_IND_MAX =  160
MODEM_STATS_NSPEC =        512
MODEM_STATS_MAX_F_HZ =     4000
MODEM_STATS_MAX_F_EST =    4

# modem stats structure
class MODEMSTATS(ctypes.Structure):
    """ """
    _fields_ = [
        ("Nc", ctypes.c_int),
        ("snr_est", ctypes.c_float),
        ("rx_symbols", (ctypes.c_float * MODEM_STATS_NR_MAX)*MODEM_STATS_NC_MAX),
        ("nr", ctypes.c_int),
        ("sync", ctypes.c_int),
        ("foff", ctypes.c_float),
        ("rx_timing", ctypes.c_float),
        ("clock_offset", ctypes.c_float),
        ("sync_metric", ctypes.c_float),
        ("pre", ctypes.c_int),
        ("post", ctypes.c_int),
        ("uw_fails", ctypes.c_int),
        ("neyetr", ctypes.c_int), # How many eye traces are plotted
        ("neyesamp", ctypes.c_int), # How many samples in the eye diagram
        ("f_est", (ctypes.c_float * MODEM_STATS_MAX_F_EST)), # How many samples in the eye diagram
        ("fft_buf", (ctypes.c_float * MODEM_STATS_NSPEC * 2)),
    ]

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
    """
    thread safe audio buffer, which fits to needs of codec2

    made by David Rowe, VK5DGR
    """
    # a buffer of int16 samples, using a fixed length numpy array self.buffer for storage
    # self.nbuffer is the current number of samples in the buffer
    def __init__(self, size):
        structlog.get_logger("structlog").debug("[C2 ] creating audio buffer", size=size)
        self.size = size
        self.buffer = np.zeros(size, dtype=np.int16)
        self.nbuffer = 0
        self.mutex = Lock()

    def push(self,samples):
        """
        Push new data to buffer

        Args:
          samples:

        Returns:

        """
        self.mutex.acquire()
        # add samples at the end of the buffer
        assert self.nbuffer+len(samples) <= self.size
        self.buffer[self.nbuffer:self.nbuffer+len(samples)] = samples
        self.nbuffer += len(samples)
        self.mutex.release()

    def pop(self,size):
        """
        get data from buffer in size of NIN
        Args:
          size:

        Returns:

        """
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
    """
    resampler class
    """
    # resample an array of variable length, we just store the filter memories here
    MEM8 = api.FDMDV_OS_TAPS_48_8K
    MEM48 = api.FDMDV_OS_TAPS_48K

    def __init__(self):
        structlog.get_logger("structlog").debug("[C2 ] create 48<->8 kHz resampler")
        self.filter_mem8 = np.zeros(self.MEM8, dtype=np.int16)
        self.filter_mem48 = np.zeros(self.MEM48)

    def resample48_to_8(self,in48):
        """
        audio resampler integration from codec2
        downsample audio from 48000Hz to 8000Hz
        Args:
          in48: input data as np.int16

        Returns: downsampled 8000Hz data as np.int16

        """
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
        """
        audio resampler integration from codec2
        resample audio from 8000Hz to 48000Hz
        Args:
          in8: input data as np.int16

        Returns: 48000Hz audio as np.int16

        """
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
