#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Throw away test program to help understand the care and feeding of PyAudio

import pyaudio
import numpy as np

CHUNK = 1024
FS48  = 48000
FTEST = 800
AMP   = 16000

# 1. play sine wave out of default sound device

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=FS48,
                frames_per_buffer=CHUNK,
                output=True
)      

f48 = open("out48.raw", mode='wb')
t = 0;
for f in range(50):
    sine_48k = (AMP*np.cos(2*np.pi*np.arange(t,t+CHUNK)*FTEST/FS48)).astype(np.int16)
    t += CHUNK
    sine_48k.tofile(f48)
    stream.write(sine_48k.tobytes())
    sil_48k = np.zeros(CHUNK, dtype=np.int16)
for f in range(50):
    sil_48k.tofile(f48)
    stream.write(sil_48k)
    
stream.stop_stream()
stream.close()
p.terminate()
f48.close()
