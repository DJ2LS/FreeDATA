#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Throw away test program to help understand the care and feeding of PyAudio

import numpy as np
import pyaudio

CHUNK = 1024
FS48 = 48000
FTEST = 800
AMP = 16000


def test_pa():
    # 1. play sine wave out of default sound device

    p_audio = pyaudio.PyAudio()
    stream = p_audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=FS48,
        frames_per_buffer=CHUNK,
        output=True,
    )

    with open("out48.raw", mode="wb") as f48:
        temp = 0
        for _ in range(50):
            sine_48k = (
                AMP * np.cos(2 * np.pi * np.arange(temp, temp + CHUNK) * FTEST / FS48)
            ).astype(np.int16)
            temp += CHUNK
            sine_48k.tofile(f48)
            stream.write(sine_48k.tobytes())
            sil_48k = np.zeros(CHUNK, dtype=np.int16)

        for _ in range(50):
            sil_48k.tofile(f48)
            stream.write(sil_48k)

        stream.stop_stream()
        stream.close()
        p_audio.terminate()


if __name__ == "__main__":
    test_pa()
