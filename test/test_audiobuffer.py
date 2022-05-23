#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# tests audio buffer thread safety

# pylint: disable=global-statement, invalid-name

import sys
import threading
from time import sleep

import codec2
import numpy as np
import pytest

BUFFER_SZ = 1024
N_MAX = 100  # write a repeating sequence of 0..N_MAX-1
WRITE_SZ = 10  # different read and write sized buffers
READ_SZ = 8
NTESTS = 10000

running = True
audio_buffer = codec2.audio_buffer(BUFFER_SZ)

n_write = 0


def t_writer():
    """
    Subprocess to handle writes to the NumPY audio "device."
    """
    global n_write
    print("writer starting")
    n = 0
    buf = np.zeros(WRITE_SZ, dtype=np.int16)
    while running:
        nfree = audio_buffer.size - audio_buffer.nbuffer
        if nfree >= WRITE_SZ:
            for index in range(WRITE_SZ):
                buf[index] = n
                n += 1
                if n == N_MAX:
                    n = 0
                n_write += 1
            audio_buffer.push(buf)


def test_audiobuffer():
    """
    Test for the audiobuffer
    """
    global running

    # Start the writer in a new thread.
    writer_thread = threading.Thread(target=t_writer)
    writer_thread.start()

    n_out = n_read = errors = 0
    for _ in range(NTESTS):
        while audio_buffer.nbuffer < READ_SZ:
            sleep(0.001)
        for i in range(READ_SZ):
            if audio_buffer.buffer[i] != n_out:
                errors += 1
            n_out += 1
            if n_out == N_MAX:
                n_out = 0
            n_read += 1
        audio_buffer.pop(READ_SZ)

    print(f"n_write: {n_write} n_read: {n_read} errors: {errors} ")

    # Indirectly stop the thread
    running = False
    sleep(0.1)

    assert not writer_thread.is_alive()
    assert n_write - n_read < BUFFER_SZ
    assert errors == 0


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-v", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
