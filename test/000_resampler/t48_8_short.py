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

# Due to the design of these resamplers, the processing buffer (at 8kHz)
# must be an integer multiple of oversampling ratio
assert N8 % FDMDV_OS_48 == 0

in8k = np.zeros(MEM8 + N8, dtype=np.int16)
out48k = np.zeros(N48, dtype=np.int16)
in48k = np.zeros(MEM48 + N48, dtype=np.int16)
out8k = np.zeros(N8, dtype=np.int16)

# time indexes, we advance every frame
t = 0
t1 = 0

fin8 = open("in8.raw", mode='wb')
f48 = open("out48.raw", mode='wb')
fout8 = open("out8.raw", mode='wb')

for f in range(FRAMES):

    # input sine wave
    in8k[MEM8:] = AMP*np.cos(2*np.pi*np.arange(t,t+N8)*FTEST8/FS8)
    t += N8
    in8k[MEM8:].tofile(fin8)

    # upsample
    pin8k,flag = in8k.__array_interface__['data']
    pin8k += 2*MEM8
    codec2.api.fdmdv_8_to_48_short(out48k.ctypes, pin8k, N8);
    out48k.tofile(f48)

    # add interfering sine wave (down sampling filter should remove)
    in48k[MEM48:] = out48k + (AMP/2)*np.cos(2*np.pi*np.arange(t1,t1+N48)*FINTER48/FS48)
    t1 += N48

    # downsample
    pin48k,flag = in48k.__array_interface__['data']
    pin48k += 2*MEM48
    codec2.api.fdmdv_48_to_8_short(out8k.ctypes, pin48k, N8);
    out8k.tofile(fout8)

fin8.close()
f48.close()
fout8.close()

# Automated test evaluation --------------------------------------------

# The input and output signals will not be time aligned due to the filter
# delays, so compare the magnitude spectrum

in8k = np.fromfile("in8.raw", dtype=np.int16)
out8k = np.fromfile("out8.raw", dtype=np.int16)
assert len(in8k) == len(out8k)

n = len(in8k)

h = np.hanning(len(in8k))
S1 = np.abs(np.fft.fft(in8k * h))
S2 = np.abs(np.fft.fft(out8k * h))

error = S1-S2
error_energy = np.dot(error,error)
ratio = error_energy/np.dot(S1,S1)
ratio_dB = 10*np.log10(ratio);
print("ratio_dB: %4.2f" % (ratio_dB));
threshdB = -40
if ratio_dB < threshdB:
    print("PASS")
else:
    print("FAIL")
