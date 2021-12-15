#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Unit test for FreeDV API resampler functions, from
# codec2/unittest/t48_8_short.c - generate a sine wave at 8 KHz,
# upsample to 48 kHz, add an interferer, then downsample back to 8 kHz
#
# You can listen to the output files with:
#
#   aplay -f S16_LE in8.raw
#   aplay -r 48000 -f S16_LE out48.raw
#   aplay -f S16_LE out8.raw
#
# They should sound like clean sine waves

import ctypes
from ctypes import *
import pathlib
import argparse
import sys
sys.path.insert(0,'..')
import codec2
import numpy as np

# dig some constants out
FDMDV_OS_48 = codec2.api.FDMDV_OS_48
FDMDV_OS_TAPS_48K = codec2.api.FDMDV_OS_TAPS_48K 
FDMDV_OS_TAPS_48_8K = codec2.api.FDMDV_OS_TAPS_48_8K

N8       = int(180)                   # processing buffer size at 8 kHz
N48      = int(N8*FDMDV_OS_48)        # processing buffer size at 48 kHz
MEM8     = int(FDMDV_OS_TAPS_48_8K)   # 8kHz signal filter memory
MEM48    = int(FDMDV_OS_TAPS_48K)     # 48kHz signal filter memory
FRAMES   = int(50)                    # number of frames to test
FS8      = 8000
FS48     = 48000
AMP      = 16000                      # sine wave amplitude
FTEST8   = 800                        # input test frequency at FS=8kHz
FINTER48 = 10000                      # interferer frequency at FS=48kHz

in8k = np.zeros(MEM8 + N8, dtype=np.int16)
out48k = np.zeros(N48, dtype=np.int16)
in48k = np.zeros(MEM48 + N48, dtype=np.int16)
out8k = np.zeros(N8, dtype=np.int16)

t = 0
fin8 = open("in8.raw", mode='wb')
f48 = open("out48.raw", mode='wb')

for f in range(FRAMES):
    
    in8k[MEM8:] = AMP*np.cos(2*np.pi*np.arange(t,t+N8)*FTEST8/FS8)
    t += N8
    in8k[MEM8:].tofile(fin8)

    pin8k,flag = in8k.__array_interface__['data']
    pin8k += 2*MEM8
    codec2.api.fdmdv_8_to_48_short(out48k.ctypes, pin8k, N8);
    out48k.tofile(f48)

fin8.close()
f48.close()
