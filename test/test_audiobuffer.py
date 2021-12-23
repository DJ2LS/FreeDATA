#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# tests audio buffer thread safety

import sys
sys.path.insert(0,'..')
from tnc import codec2
import threading
import numpy as np
from time import sleep

BUFFER_SZ = 1024
N_MAX     = 100     # write a repeating sequence of 0..N_MAX-1
WRITE_SZ  = 10      # different read and write sized buffers
READ_SZ   = 8
NTESTS    = 10000

running = True
audio_buffer = codec2.audio_buffer(BUFFER_SZ)

n_write = int(0)
n_read = int(0)

def writer():
    global n_write
    print("writer starting")
    n = int(0)
    buf = np.zeros(WRITE_SZ, dtype=np.int16)
    while running:
        nfree = audio_buffer.size - audio_buffer.nbuffer
        if nfree >= WRITE_SZ:
            for i in range(0,WRITE_SZ):
                buf[i] = n;
                n += 1
                if n == N_MAX:
                    n = 0
                n_write += 1
            audio_buffer.push(buf)
        
x = threading.Thread(target=writer)
x.start()

n_out = int(0)
errors = int(0)
for tests in range(1,NTESTS):
    while audio_buffer.nbuffer < READ_SZ:
        sleep(0.001)
    for i in range(0,READ_SZ):
        if audio_buffer.buffer[i] != n_out:
            errors += 1
        n_out += 1
        if n_out == N_MAX:
            n_out = 0
        n_read += 1
    audio_buffer.pop(READ_SZ)

running = False
print("n_write: %d n_read: %d errors: %d " % (n_write, n_read, errors))
