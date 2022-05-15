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

# pylint: disable=global-statement, invalid-name, unused-import

import os
import sys

import codec2
import numpy as np
import pytest

# dig some constants out
FDMDV_OS_48 = codec2.api.FDMDV_OS_48
FDMDV_OS_TAPS_48K = codec2.api.FDMDV_OS_TAPS_48K
FDMDV_OS_TAPS_48_8K = codec2.api.FDMDV_OS_TAPS_48_8K

N8 = 180  # processing buffer size at 8 kHz
N48 = N8 * FDMDV_OS_48  # processing buffer size at 48 kHz
MEM8 = FDMDV_OS_TAPS_48_8K  # 8kHz signal filter memory
MEM48 = FDMDV_OS_TAPS_48K  # 48kHz signal filter memory
FRAMES = 50  # number of frames to test
FS8 = 8000
FS48 = 48000
AMP = 16000  # sine wave amplitude
FTEST8 = 800  # input test frequency at FS=8kHz
FINTER48 = 10000  # interferer frequency at FS=48kHz

# Due to the design of these resamplers, the processing buffer (at 8kHz)
# must be an integer multiple of oversampling ratio
assert N8 % FDMDV_OS_48 == 0


def test_resampler():
    """
    Test for the codec2 audio resampling routine
    """
    # time indexes, we advance every frame
    t = 0
    t1 = 0

    # output files to listen to/evaluate result
    with open("in8.raw", mode="wb") as fin8:
        with open("out48.raw", mode="wb") as f48:
            with open("out8.raw", mode="wb") as fout8:
                resampler = codec2.resampler()

                # Generate FRAMES of a sine wave
                for _ in range(FRAMES):
                    # Primary sine wave, which the down-sampling filter should retain.
                    sine_in8k = (
                        AMP * np.cos(2 * np.pi * np.arange(t, t + N8) * FTEST8 / FS8)
                    ).astype(np.int16)
                    t += N8
                    sine_in8k.tofile(fin8)

                    sine_out48k = resampler.resample8_to_48(sine_in8k)
                    sine_out48k.tofile(f48)

                    # Add an interfering sine wave, which the down-sampling filter should (mostly) remove
                    sine_in48k = (
                        sine_out48k
                        + (AMP / 2)
                        * np.cos(2 * np.pi * np.arange(t1, t1 + N48) * FINTER48 / FS48)
                    ).astype(np.int16)
                    t1 += N48

                    sine_out8k = resampler.resample48_to_8(sine_in48k)
                    sine_out8k.tofile(fout8)

    # os.unlink("out48.raw")

    # Automated test evaluation --------------------------------------------

    # The input and output signals will not be time aligned due to the filter
    # delays, so compare the magnitude spectrum

    # Read the raw audio files
    in8k = np.fromfile("in8.raw", dtype=np.int16)
    out8k = np.fromfile("out8.raw", dtype=np.int16)
    assert len(in8k) == len(out8k)
    # os.unlink("in8.raw")
    # os.unlink("out8.raw")

    # Apply hanning filter to raw input data samples
    h = np.hanning(len(in8k))
    S1 = np.abs(np.fft.fft(in8k * h))
    S2 = np.abs(np.fft.fft(out8k * h))

    # Calculate the ratio between signal and noise (error energy).
    error = S1 - S2
    error_energy = np.dot(error, error)
    ratio = error_energy / np.dot(S1, S1)
    ratio_dB = 10 * np.log10(ratio)

    # Establish -40.0 as the noise ratio ceiling
    threshdB = -40.0
    print(f"ratio_dB: {ratio_dB:4.2}" % (ratio_dB))
    assert ratio_dB < threshdB


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-v", sys.argv[0]])
    if ecode == 0:
        print("PASS")
    else:
        print("FAIL")
