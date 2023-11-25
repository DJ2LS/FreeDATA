"""
Python interface to the C-language codec2 library.
"""
# -*- coding: utf-8 -*-

# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel, attribute-defined-outside-init

import ctypes
import glob
import os
import sys
from enum import Enum
from threading import Lock

import numpy as np
import structlog

log = structlog.get_logger("codec2")


# Enum for codec2 modes
class FREEDV_MODE(Enum):
    """
    Enumeration for codec2 modes and names
    """
    sig0 = 19
    sig1 = 19
    datac0 = 14
    datac1 = 10
    datac3 = 12
    datac4 = 18
    datac13 = 19
    fsk_ldpc = 9
    fsk_ldpc_0 = 200
    fsk_ldpc_1 = 201


class FREEDV_MODE_USED_SLOTS(Enum):
    """
    Enumeration for codec2 used slots
    """
    sig0 = [False, False, True, False, False]
    sig1 = [False, False, True, False, False]
    datac0 = [False, False, True, False, False]
    datac1 = [False, True, True, True, False]
    datac3 = [False, False, True, False, False]
    datac4 = [False, False, True, False, False]
    datac13 = [False, False, True, False, False]
    fsk_ldpc = [False, False, True, False, False]
    fsk_ldpc_0 = [False, False, True, False, False]
    fsk_ldpc_1 = [False, False, True, False, False]

# Function for returning the mode value
def freedv_get_mode_value_by_name(mode: str) -> int:
    """
    Get the codec2 mode by entering its string

    Args:
        mode: String representation of the codec2 mode.

    Returns:
        int
    """
    return FREEDV_MODE[mode.lower()].value


# Function for returning the mode name
def freedv_get_mode_name_by_value(mode: int) -> str:
    """
    Get the codec2 mode name as string
    Args:
        mode: Integer value of the codec2 mode.

    Returns:
        string
    """
    return FREEDV_MODE(mode).name


# Check if we are running in a pyinstaller environment
#if hasattr(sys, "_MEIPASS"):
#    sys.path.append(getattr(sys, "_MEIPASS"))
#else:
sys.path.append(os.path.abspath("."))

#log.info("[C2 ] Searching for libcodec2...")
if sys.platform == "linux":
    files = glob.glob(r"**/*libcodec2*", recursive=True)
    files.append("libcodec2.so")
elif sys.platform == "darwin":
    if hasattr(sys, "_MEIPASS"):
        files = glob.glob(getattr(sys, "_MEIPASS") + '/**/*libcodec2*', recursive=True)
    else:
        files = glob.glob(r"**/*libcodec2*.dylib", recursive=True)
elif sys.platform in ["win32", "win64"]:
    files = glob.glob(r"**\*libcodec2*.dll", recursive=True)
else:
    files = []

api = None
for file in files:
    try:
        api = ctypes.CDLL(file)
        #log.info("[C2 ] Libcodec2 loaded", path=file)
        break
    except OSError as err:
        log.warning("[C2 ] Error:  Libcodec2 found but not loaded", path=file, e=err)

# Quit module if codec2 cant be loaded
if api is None or "api" not in locals():
    log.critical("[C2 ] Error:  Libcodec2 not loaded - Exiting")
    sys.exit(1)

# ctypes function init

# api.freedv_set_tuning_range.restype = ctypes.c_int
# api.freedv_set_tuning_range.argype = [ctypes.c_void_p, ctypes.c_float, ctypes.c_float]

api.freedv_open.argype = [ctypes.c_int]  # type: ignore
api.freedv_open.restype = ctypes.c_void_p

api.freedv_set_sync.argype = [ctypes.c_void_p, ctypes.c_int]  # type: ignore
api.freedv_set_sync.restype = ctypes.c_void_p

api.freedv_open_advanced.argtype = [ctypes.c_int, ctypes.c_void_p]  # type: ignore
api.freedv_open_advanced.restype = ctypes.c_void_p

api.freedv_get_bits_per_modem_frame.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_get_bits_per_modem_frame.restype = ctypes.c_int

api.freedv_get_modem_extended_stats.argtype = [ctypes.c_void_p, ctypes.c_void_p]
api.freedv_get_modem_extended_stats.restype = ctypes.c_int

api.freedv_nin.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_nin.restype = ctypes.c_int

api.freedv_rawdatarx.argtype = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]  # type: ignore
api.freedv_rawdatarx.restype = ctypes.c_int

api.freedv_rawdatatx.argtype = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]  # type: ignore
api.freedv_rawdatatx.restype = ctypes.c_int

api.freedv_rawdatapostambletx.argtype = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]  # type: ignore
api.freedv_rawdatapostambletx.restype = ctypes.c_int

api.freedv_rawdatapreambletx.argtype = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]  # type: ignore
api.freedv_rawdatapreambletx.restype = ctypes.c_int

api.freedv_get_n_max_modem_samples.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_get_n_max_modem_samples.restype = ctypes.c_int

api.freedv_set_frames_per_burst.argtype = [ctypes.c_void_p, ctypes.c_int]  # type: ignore
api.freedv_set_frames_per_burst.restype = ctypes.c_void_p

api.freedv_get_rx_status.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_get_rx_status.restype = ctypes.c_int

api.freedv_get_modem_stats.argtype = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]  # type: ignore
api.freedv_get_modem_stats.restype = ctypes.c_int

api.freedv_get_n_tx_postamble_modem_samples.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_get_n_tx_postamble_modem_samples.restype = ctypes.c_int

api.freedv_get_n_tx_preamble_modem_samples.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_get_n_tx_preamble_modem_samples.restype = ctypes.c_int

api.freedv_get_n_tx_modem_samples.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_get_n_tx_modem_samples.restype = ctypes.c_int

api.freedv_get_n_max_modem_samples.argtype = [ctypes.c_void_p]  # type: ignore
api.freedv_get_n_max_modem_samples.restype = ctypes.c_int

api.FREEDV_FS_8000 = 8000  # type: ignore

# -------------------------------- FSK LDPC MODE SETTINGS


class ADVANCED(ctypes.Structure):
    """Advanced structure for fsk modes"""

    _fields_ = [
        ("interleave_frames", ctypes.c_int),
        ("M", ctypes.c_int),
        ("Rs", ctypes.c_int),
        ("Fs", ctypes.c_int),
        ("first_tone", ctypes.c_int),
        ("tone_spacing", ctypes.c_int),
        ("codename", ctypes.c_char_p),
    ]


# pylint: disable=pointless-string-statement
"""
adv.interleave_frames = 0                       # max amplitude
adv.M = 2                                       # number of fsk tones 2/4
adv.Rs = 100                                    # symbol rate
adv.Fs = 8000                                   # sample rate
adv.first_tone = 1500                           # first tone freq
adv.tone_spacing = 200                          # shift between tones
adv.codename = "H_128_256_5".encode("utf-8")    # code word

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
"""
# --------------- 2 FSK H_128_256_5, 16 bytes
api.FREEDV_MODE_FSK_LDPC_0_ADV = ADVANCED()  # type: ignore
api.FREEDV_MODE_FSK_LDPC_0_ADV.interleave_frames = 0
api.FREEDV_MODE_FSK_LDPC_0_ADV.M = 4
api.FREEDV_MODE_FSK_LDPC_0_ADV.Rs = 500
api.FREEDV_MODE_FSK_LDPC_0_ADV.Fs = 8000
api.FREEDV_MODE_FSK_LDPC_0_ADV.first_tone = 1150  # 1150 4fsk, 1500 2fsk
api.FREEDV_MODE_FSK_LDPC_0_ADV.tone_spacing = 200  # 200
api.FREEDV_MODE_FSK_LDPC_0_ADV.codename = "H_128_256_5".encode("utf-8")  # code word

# --------------- 4 H_256_512_4, 7 bytes
api.FREEDV_MODE_FSK_LDPC_1_ADV = ADVANCED()  # type: ignore
api.FREEDV_MODE_FSK_LDPC_1_ADV.interleave_frames = 0
api.FREEDV_MODE_FSK_LDPC_1_ADV.M = 4
api.FREEDV_MODE_FSK_LDPC_1_ADV.Rs = 1000
api.FREEDV_MODE_FSK_LDPC_1_ADV.Fs = 8000
api.FREEDV_MODE_FSK_LDPC_1_ADV.first_tone = 1150  # 1250 4fsk, 1500 2fsk
api.FREEDV_MODE_FSK_LDPC_1_ADV.tone_spacing = 200
api.FREEDV_MODE_FSK_LDPC_1_ADV.codename = "H_4096_8192_3d".encode("utf-8")  # code word

# ------- MODEM STATS STRUCTURES
MODEM_STATS_NC_MAX = 50 + 1 * 2
MODEM_STATS_NR_MAX = 320 * 2
MODEM_STATS_ET_MAX = 8
MODEM_STATS_EYE_IND_MAX = 160
MODEM_STATS_NSPEC = 512
MODEM_STATS_MAX_F_HZ = 4000
MODEM_STATS_MAX_F_EST = 4


class MODEMSTATS(ctypes.Structure):
    """Modem statistics structure"""

    _fields_ = [
        ("Nc", ctypes.c_int),
        ("snr_est", ctypes.c_float),
        ("rx_symbols", (ctypes.c_float * MODEM_STATS_NR_MAX) * MODEM_STATS_NC_MAX),
        ("nr", ctypes.c_int),
        ("sync", ctypes.c_int),
        ("foff", ctypes.c_float),
        ("rx_timing", ctypes.c_float),
        ("clock_offset", ctypes.c_float),
        ("sync_metric", ctypes.c_float),
        ("pre", ctypes.c_int),
        ("post", ctypes.c_int),
        ("uw_fails", ctypes.c_int),
        ("rx_eye", (ctypes.c_float * MODEM_STATS_ET_MAX) * MODEM_STATS_EYE_IND_MAX),
        ("neyetr", ctypes.c_int),  # How many eye traces are plotted
        ("neyesamp", ctypes.c_int),  # How many samples in the eye diagram
        ("f_est", (ctypes.c_float * MODEM_STATS_MAX_F_EST)),
        ("fft_buf", (ctypes.c_float * MODEM_STATS_NSPEC * 2)),
        ("fft_cfg", ctypes.c_void_p)
    ]


# Return code flags for freedv_get_rx_status() function
api.FREEDV_RX_TRIAL_SYNC = 0x1  # type: ignore # demodulator has trial sync
api.FREEDV_RX_SYNC = 0x2  # type: ignore # demodulator has sync
api.FREEDV_RX_BITS = 0x4  # type: ignore # data bits have been returned
api.FREEDV_RX_BIT_ERRORS = 0x8  # type: ignore # FEC may not have corrected all bit errors (not all parity checks OK)

api.rx_sync_flags_to_text = [  # type: ignore
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
    "EBST",
]

# Audio buffer ---------------------------------------------------------
class audio_buffer:
    """
    Thread-safe audio buffer, which fits the needs of codec2

    made by David Rowe, VK5DGR
    """

    # A buffer of int16 samples, using a fixed length numpy array self.buffer for storage
    # self.nbuffer is the current number of samples in the buffer
    def __init__(self, size):
        log.debug("[C2 ] Creating audio buffer", size=size)
        self.size = size
        self.buffer = np.zeros(size, dtype=np.int16)
        self.nbuffer = 0
        self.mutex = Lock()

    def push(self, samples):
        """
        Push new data to buffer

        Args:
            samples:

        Returns:
            Nothing
        """
        self.mutex.acquire()
        # Add samples at the end of the buffer
        assert self.nbuffer + len(samples) <= self.size
        self.buffer[self.nbuffer : self.nbuffer + len(samples)] = samples
        self.nbuffer += len(samples)
        self.mutex.release()

    def pop(self, size):
        """
        get data from buffer in size of NIN
        Args:
          size:

        Returns:
            Nothing
        """
        self.mutex.acquire()
        # Remove samples from the start of the buffer
        self.nbuffer -= size
        self.buffer[: self.nbuffer] = self.buffer[size : size + self.nbuffer]
        assert self.nbuffer >= 0
        self.mutex.release()


# Resampler ---------------------------------------------------------

# Oversampling rate
api.FDMDV_OS_48 = 6  # type: ignore
# Number of oversampling taps at 48kHz
api.FDMDV_OS_TAPS_48K = 48  # type: ignore
# Number of oversampling filter taps at 8kHz
api.FDMDV_OS_TAPS_48_8K = api.FDMDV_OS_TAPS_48K // api.FDMDV_OS_48  # type: ignore
api.fdmdv_8_to_48_short.argtype = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]  # type: ignore
api.fdmdv_48_to_8_short.argtype = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]  # type: ignore


class resampler:
    """
    Re-sampler class
    """

    # Re-sample an array of variable length, we just store the filter memories here
    MEM8 = api.FDMDV_OS_TAPS_48_8K
    MEM48 = api.FDMDV_OS_TAPS_48K

    def __init__(self):
        log.debug("[C2 ] Create 48<->8 kHz resampler")
        self.filter_mem8 = np.zeros(self.MEM8, dtype=np.int16)
        self.filter_mem48 = np.zeros(self.MEM48)

    def resample48_to_8(self, in48):
        """
        Audio resampler integration from codec2
        Downsample audio from 48000Hz to 8000Hz
        Args:
            in48: input data as np.int16

        Returns:
            Downsampled 8000Hz data as np.int16
        """
        assert in48.dtype == np.int16
        # Length of input vector must be an integer multiple of api.FDMDV_OS_48
        assert len(in48) % api.FDMDV_OS_48 == 0  # type: ignore

        # Concatenate filter memory and input samples
        in48_mem = np.zeros(self.MEM48 + len(in48), dtype=np.int16)
        in48_mem[: self.MEM48] = self.filter_mem48
        in48_mem[self.MEM48 :] = in48

        # In C: pin48=&in48_mem[MEM48]
        pin48 = ctypes.byref(np.ctypeslib.as_ctypes(in48_mem), 2 * self.MEM48)
        n8 = int(len(in48) / api.FDMDV_OS_48)  # type: ignore
        out8 = np.zeros(n8, dtype=np.int16)
        api.fdmdv_48_to_8_short(out8.ctypes, pin48, n8)  # type: ignore

        # Store memory for next time
        self.filter_mem48 = in48_mem[: self.MEM48]

        return out8

    def resample8_to_48(self, in8):
        """
        Audio resampler integration from codec2
        Re-sample audio from 8000Hz to 48000Hz
        Args:
            in8: input data as np.int16

        Returns:
            48000Hz audio as np.int16
        """
        assert in8.dtype == np.int16

        # Concatenate filter memory and input samples
        in8_mem = np.zeros(self.MEM8 + len(in8), dtype=np.int16)
        in8_mem[: self.MEM8] = self.filter_mem8
        in8_mem[self.MEM8 :] = in8

        # In C: pin8=&in8_mem[MEM8]
        pin8 = ctypes.byref(np.ctypeslib.as_ctypes(in8_mem), 2 * self.MEM8)
        out48 = np.zeros(api.FDMDV_OS_48 * len(in8), dtype=np.int16)  # type: ignore
        api.fdmdv_8_to_48_short(out48.ctypes, pin8, len(in8))  # type: ignore

        # Store memory for next time
        self.filter_mem8 = in8_mem[: self.MEM8]

        return out48

def open_instance(mode: int) -> ctypes.c_void_p:
    """
    Return a codec2 instance of the type `mode`

    :param mode: Type of codec2 instance to return
    :type mode: Union[int, str]
    :return: C-function of the requested codec2 instance
    :rtype: ctypes.c_void_p
    """
    if mode in [FREEDV_MODE.fsk_ldpc_0.value]:
        return ctypes.cast(
            api.freedv_open_advanced(
                FREEDV_MODE.fsk_ldpc.value,
                ctypes.byref(api.FREEDV_MODE_FSK_LDPC_0_ADV),
            ),
            ctypes.c_void_p,
        )

    if mode in [FREEDV_MODE.fsk_ldpc_1.value]:
        return ctypes.cast(
            api.freedv_open_advanced(
                FREEDV_MODE.fsk_ldpc.value,
                ctypes.byref(api.FREEDV_MODE_FSK_LDPC_1_ADV),
            ),
            ctypes.c_void_p,
        )

    return ctypes.cast(api.freedv_open(mode), ctypes.c_void_p)

def get_bytes_per_frame(mode: int) -> int:
    """
    Provide bytes per frame information for accessing from data handler

    :param mode: Codec2 mode to query
    :type mode: int or str
    :return: Bytes per frame of the supplied codec2 data mode
    :rtype: int
    """
    freedv = open_instance(mode)
    # TODO add close session
    # get number of bytes per frame for mode
    return int(api.freedv_get_bits_per_modem_frame(freedv) / 8)
