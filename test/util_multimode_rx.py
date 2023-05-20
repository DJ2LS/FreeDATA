#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Receive-side station emulator for test frame tests over a high quality audio channel
using a physical sound card or STDIO.

Legacy test for sending / receiving connection test frames through the codec2 and
back through on the other station. Data injection initiates directly through
the codec2 API. Tests all three codec2 data frames simultaneously.

Invoked from CMake, test_highsnr_stdio_P_P_multi.py, and many test_virtual[1-3]*.sh.

@author: DJ2LS
"""

import argparse
import ctypes
import sys
import time
from typing import List

import numpy as np
import pyaudio

sys.path.insert(0, "..")
from tnc import codec2


def test_mm_rx():
    # AUDIO PARAMETERS
    AUDIO_FRAMES_PER_BUFFER = 2400 * 2
    MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
    AUDIO_SAMPLE_RATE_RX = 48000
    # make sure our resampler will work
    assert (AUDIO_SAMPLE_RATE_RX / MODEM_SAMPLE_RATE) == codec2.api.FDMDV_OS_48

    # SET COUNTERS
    rx_bursts_datac = [0, 0, 0]
    rx_frames_datac = [0, 0, 0]
    rx_total_frames_datac = [0, 0, 0]

    # time meassurement
    time_end_datac = [0.0, 0.0, 0.0]
    time_needed_datac = [0.0, 0.0, 0.0]
    time_start_datac = [0.0, 0.0, 0.0]

    datac_buffer: List[codec2.audio_buffer] = []
    datac_bytes_out: List[ctypes.Array] = []
    datac_bytes_per_frame = []
    datac_freedv: List[ctypes.c_void_p] = []

    args = parse_arguments()

    if args.LIST:
        p_audio = pyaudio.PyAudio()
        for dev in range(p_audio.get_device_count()):
            print("audiodev: ", dev, p_audio.get_device_info_by_index(dev)["name"])
        sys.exit()

    N_BURSTS = args.N_BURSTS
    N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
    AUDIO_INPUT_DEVICE = args.AUDIO_INPUT_DEVICE
    DEBUGGING_MODE = args.DEBUGGING_MODE
    MAX_TIME = args.TIMEOUT

    # open codec2 instances
    for idx in range(3):
        datac_freedv.append(
            ctypes.cast(
                codec2.api.freedv_open(codec2.FREEDV_MODE.datac13.value), ctypes.c_void_p
            )
        )
        datac_bytes_per_frame.append(
            int(codec2.api.freedv_get_bits_per_modem_frame(datac_freedv[idx]) / 8)
        )
        datac_bytes_out.append(ctypes.create_string_buffer(datac_bytes_per_frame[idx]))
        codec2.api.freedv_set_frames_per_burst(datac_freedv[idx], N_FRAMES_PER_BURST)
        datac_buffer.append(codec2.audio_buffer(2 * AUDIO_FRAMES_PER_BUFFER))

    resampler = codec2.resampler()

    # check if we want to use an audio device then do a pyaudio init
    if AUDIO_INPUT_DEVICE != -1:
        p_audio = pyaudio.PyAudio()
        # auto search for loopback devices
        if AUDIO_INPUT_DEVICE == -2:
            loopback_list = [
                dev
                for dev in range(p_audio.get_device_count())
                if "Loopback: PCM" in p_audio.get_device_info_by_index(dev)["name"]
            ]

            if len(loopback_list) >= 2:
                AUDIO_INPUT_DEVICE = loopback_list[0]  # 0  = RX   1 = TX
                print(f"loopback_list rx: {loopback_list}", file=sys.stderr)
            else:
                sys.exit()

        print(
            f"AUDIO INPUT DEVICE: {AUDIO_INPUT_DEVICE} "
            f"DEVICE: {p_audio.get_device_info_by_index(AUDIO_INPUT_DEVICE)['name']} "
            f"AUDIO SAMPLE RATE: {AUDIO_SAMPLE_RATE_RX}",
            file=sys.stderr,
        )
        stream_rx = p_audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=AUDIO_SAMPLE_RATE_RX,
            frames_per_buffer=AUDIO_FRAMES_PER_BUFFER,
            input=True,
            input_device_index=AUDIO_INPUT_DEVICE,
        )

    timeout = time.time() + MAX_TIME
    print(time.time(), MAX_TIME, timeout)
    receive = True
    nread_exceptions = 0

    # initial nin values
    datac_nin = [0, 0, 0]
    for idx in range(3):
        datac_nin[idx] = codec2.api.freedv_nin(datac_freedv[idx])

    def print_stats(time_datac13, time_datac1, time_datac3):
        if not DEBUGGING_MODE:
            return

        time_datac = [time_datac13, time_datac1, time_datac3]
        datac_rxstatus = ["", "", ""]
        for idx in range(3):
            datac_rxstatus[idx] = codec2.api.rx_sync_flags_to_text[
                codec2.api.freedv_get_rx_status(datac_freedv[idx])
            ]

        text_out = ""
        for idx in range(3):
            text_out += f"NIN{idx}: {datac_nin[idx]:5d} "
            text_out += f"RX_STATUS{idx}: {datac_rxstatus[idx]:4s} "
            text_out += f"TIME: {round(time_datac[idx], 4):.4f} | "
        text_out = text_out.rstrip(" ").rstrip("|").rstrip(" ")
        print(text_out, file=sys.stderr)

    while receive and time.time() < timeout:
        if AUDIO_INPUT_DEVICE != -1:
            try:
                data_in48k = stream_rx.read(
                    AUDIO_FRAMES_PER_BUFFER, exception_on_overflow=True
                )
            except OSError as err:
                print(err, file=sys.stderr)
                if "Input overflowed" in str(err):
                    nread_exceptions += 1
                if "Stream closed" in str(err):
                    print("Ending....")
                    receive = False
        else:
            data_in48k = sys.stdin.buffer.read(AUDIO_FRAMES_PER_BUFFER * 2)

        # insert samples in buffer
        audio_buffer = np.frombuffer(data_in48k, dtype=np.int16)
        if len(audio_buffer) != AUDIO_FRAMES_PER_BUFFER:
            print("len(x)", len(audio_buffer))
            receive = False
        audio_buffer = resampler.resample48_to_8(audio_buffer)

        for idx in range(3):
            datac_buffer[idx].push(audio_buffer)
            while datac_buffer[idx].nbuffer >= datac_nin[idx]:
                # demodulate audio
                time_start_datac[idx] = time.time()
                nbytes = codec2.api.freedv_rawdatarx(
                    datac_freedv[idx],
                    datac_bytes_out[idx],
                    datac_buffer[idx].buffer.ctypes,
                )
                time_end_datac[idx] = time.time()
                datac_buffer[idx].pop(datac_nin[idx])
                datac_nin[idx] = codec2.api.freedv_nin(datac_freedv[idx])
                if nbytes == datac_bytes_per_frame[idx]:
                    rx_total_frames_datac[idx] += 1
                    rx_frames_datac[idx] += 1

                    if rx_frames_datac[idx] == N_FRAMES_PER_BURST:
                        rx_frames_datac[idx] = 0
                        rx_bursts_datac[idx] += 1
                time_needed_datac[idx] = time_end_datac[idx] - time_start_datac[idx]
                print_stats(
                    time_needed_datac[0], time_needed_datac[1], time_needed_datac[2]
                )

        if (
            rx_bursts_datac[0] == N_BURSTS
            and rx_bursts_datac[1] == N_BURSTS
            and rx_bursts_datac[2] == N_BURSTS
        ):
            receive = False

    if nread_exceptions:
        print(
            f"nread_exceptions {nread_exceptions:d} - receive audio lost! "
            "Consider increasing Pyaudio frames_per_buffer...",
            file=sys.stderr,
        )
    # INFO IF WE REACHED TIMEOUT
    if time.time() > timeout:
        print("TIMEOUT REACHED", file=sys.stderr)

    print(
        f"DATAC13: {rx_bursts_datac[0]}/{rx_total_frames_datac[0]} "
        f"DATAC1: {rx_bursts_datac[1]}/{rx_total_frames_datac[1]} "
        f"DATAC3: {rx_bursts_datac[2]}/{rx_total_frames_datac[2]}",
        file=sys.stderr,
    )

    if AUDIO_INPUT_DEVICE != -1:
        stream_rx.close()
        p_audio.terminate()


def parse_arguments():
    # --------------------------------------------GET PARAMETER INPUTS
    parser = argparse.ArgumentParser(description="Simons TEST TNC")
    parser.add_argument("--bursts", dest="N_BURSTS", default=1, type=int)
    parser.add_argument(
        "--framesperburst", dest="N_FRAMES_PER_BURST", default=1, type=int
    )
    parser.add_argument(
        "--audiodev",
        dest="AUDIO_INPUT_DEVICE",
        default=-1,
        type=int,
        help="audio device number to use",
    )
    parser.add_argument("--debug", dest="DEBUGGING_MODE", action="store_true")
    parser.add_argument(
        "--list",
        dest="LIST",
        action="store_true",
        help="list audio devices by number and exit",
    )
    parser.add_argument(
        "--timeout",
        dest="TIMEOUT",
        default=60,
        type=int,
        help="Timeout (seconds) before test ends",
    )

    args, _ = parser.parse_known_args()
    return args


if __name__ == "__main__":
    test_mm_rx()
