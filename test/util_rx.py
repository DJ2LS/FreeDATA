#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Receive-side station emulator for test frame tests over a high quality audio channel
using a physical sound card or STDIO.

Legacy test for sending / receiving connection test frames through the codec2 and
back through on the other station. Data injection initiates directly through
the codec2 API.

Invoked from CMake, test_highsnr_stdio_{P_C, P_P}_datacx.py, and many test_virtual[1-3]*.sh.

@author: DJ2LS
"""

import argparse
import ctypes
import sys
import time

import numpy as np
import sounddevice as sd

# pylint: disable=wrong-import-position
sys.path.insert(0, "..")
sys.path.insert(0, "../tnc")
from tnc import codec2


def util_rx():
    args = parse_arguments()

    if args.LIST:

        devices = sd.query_devices(device=None, kind=None)
        for index, device in enumerate(devices):
            print(f"{index} {device['name']}")
            index += 1
        # pylint: disable=protected-access
        sd._terminate()
        sys.exit()

    N_BURSTS = args.N_BURSTS
    N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
    AUDIO_INPUT_DEVICE = args.AUDIO_INPUT_DEVICE
    MODE = codec2.FREEDV_MODE[args.FREEDV_MODE].value
    DEBUGGING_MODE = args.DEBUGGING_MODE
    MAX_TIME = args.TIMEOUT

    # AUDIO PARAMETERS
    # v-- consider increasing if you get nread_exceptions > 0
    AUDIO_FRAMES_PER_BUFFER = 2400 * 2
    MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
    AUDIO_SAMPLE_RATE_RX = 48000

    # make sure our resampler will work
    assert (AUDIO_SAMPLE_RATE_RX / MODEM_SAMPLE_RATE) == codec2.api.FDMDV_OS_48  # type: ignore

    # check if we want to use an audio device then do a pyaudio init
    if AUDIO_INPUT_DEVICE != -1:
        # auto search for loopback devices
        if AUDIO_INPUT_DEVICE == -2:
            loopback_list = []

            devices = sd.query_devices(device=None, kind=None)

            for index, device in enumerate(devices):
                if "Loopback: PCM" in device["name"]:
                    print(index)
                    loopback_list.append(index)

            if loopback_list:
                # 0  = RX   1 = TX
                AUDIO_INPUT_DEVICE = loopback_list[0]
                print(f"loopback_list tx: {loopback_list}", file=sys.stderr)
            else:
                print("not enough audio loopback devices ready...")
                print("you should wait about 30 seconds...")

                sd._terminate()
                sys.exit()
        print(f"AUDIO INPUT DEVICE: {AUDIO_INPUT_DEVICE}", file=sys.stderr)

        # audio stream init
        stream_rx = sd.RawStream(
            channels=1,
            dtype="int16",
            device=AUDIO_INPUT_DEVICE,
            samplerate=AUDIO_SAMPLE_RATE_RX,
            blocksize=4800,
        )
        stream_rx.start()

    # ----------------------------------------------------------------
    # DATA CHANNEL INITIALISATION

    # open codec2 instance
    freedv = ctypes.cast(codec2.api.freedv_open(MODE), ctypes.c_void_p)

    # get number of bytes per frame for mode
    bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(freedv) / 8)
    payload_bytes_per_frame = bytes_per_frame - 2

    n_max_modem_samples = codec2.api.freedv_get_n_max_modem_samples(freedv)
    bytes_out = ctypes.create_string_buffer(bytes_per_frame)

    codec2.api.freedv_set_frames_per_burst(freedv, N_FRAMES_PER_BURST)

    total_n_bytes = 0
    rx_total_frames = 0
    rx_frames = 0
    rx_bursts = 0
    rx_errors = 0
    nread_exceptions = 0
    timeout = time.time() + MAX_TIME
    receive = True
    audio_buffer = codec2.audio_buffer(AUDIO_FRAMES_PER_BUFFER * 2)
    resampler = codec2.resampler()

    # time meassurement
    time_start = 0
    time_end = 0

    with open("rx48.raw", mode="wb") as frx:
        # initial number of samples we need
        nin = codec2.api.freedv_nin(freedv)
        while receive and time.time() < timeout:
            if AUDIO_INPUT_DEVICE != -1:
                try:
                    # data_in48k = stream_rx.read(AUDIO_FRAMES_PER_BUFFER, exception_on_overflow = True)
                    data_in48k, overflowed = stream_rx.read(AUDIO_FRAMES_PER_BUFFER)  # type: ignore
                except OSError as err:
                    print(err, file=sys.stderr)
                    # if str(err).find("Input overflowed") != -1:
                    #    nread_exceptions += 1
                    # if str(err).find("Stream closed") != -1:
                    #    print("Ending...")
                    #    receive = False
            else:
                data_in48k = sys.stdin.buffer.read(AUDIO_FRAMES_PER_BUFFER * 2)

            # insert samples in buffer
            x = np.frombuffer(data_in48k, dtype=np.int16)  # type: ignore
            # print(x)
            # x = data_in48k
            x.tofile(frx)
            if len(x) != AUDIO_FRAMES_PER_BUFFER:
                receive = False
            x = resampler.resample48_to_8(x)
            audio_buffer.push(x)

            # when we have enough samples call FreeDV Rx
            while audio_buffer.nbuffer >= nin:
                # start time measurement
                time_start = time.time()
                # demodulate audio
                nbytes = codec2.api.freedv_rawdatarx(
                    freedv, bytes_out, audio_buffer.buffer.ctypes
                )
                time_end = time.time()

                audio_buffer.pop(nin)

                # call me on every loop!
                nin = codec2.api.freedv_nin(freedv)

                rx_status = codec2.api.freedv_get_rx_status(freedv)
                if rx_status & codec2.api.FREEDV_RX_BIT_ERRORS:
                    rx_errors = rx_errors + 1
                if DEBUGGING_MODE:
                    rx_status = codec2.api.rx_sync_flags_to_text[rx_status]  # type: ignore
                    time_needed = time_end - time_start

                    print(
                        f"nin: {nin:5d} rx_status: {rx_status:4s} "
                        f"naudio_buffer: {audio_buffer.nbuffer:4d} time: {time_needed:4f}",
                        file=sys.stderr,
                    )

                if nbytes:
                    total_n_bytes += nbytes

                    if nbytes == bytes_per_frame:
                        rx_total_frames += 1
                        rx_frames += 1

                    if rx_frames == N_FRAMES_PER_BURST:
                        rx_frames = 0
                        rx_bursts += 1

                    if rx_bursts == N_BURSTS:
                        receive = False

            if time.time() >= timeout:
                print("TIMEOUT REACHED")

            time.sleep(0.01)

        if nread_exceptions:
            print(
                f"nread_exceptions {nread_exceptions:d} - receive audio lost! "
                "Consider increasing Pyaudio frames_per_buffer...",
                file=sys.stderr,
            )
        print(
            f"RECEIVED BURSTS: {rx_bursts} "
            f"RECEIVED FRAMES: {rx_total_frames} "
            f"RX_ERRORS: {rx_errors}",
            file=sys.stderr,
        )
    # and at last check if we had an opened audio instance and close it
    if AUDIO_INPUT_DEVICE != -1:
        sd._terminate()


def parse_arguments():
    # --------------------------------------------GET PARAMETER INPUTS
    parser = argparse.ArgumentParser(description="Simons TEST TNC")
    parser.add_argument("--bursts", dest="N_BURSTS", default=1, type=int)
    parser.add_argument(
        "--framesperburst", dest="N_FRAMES_PER_BURST", default=1, type=int
    )
    parser.add_argument(
        "--mode", dest="FREEDV_MODE", type=str, choices=["datac13", "datac1", "datac3"]
    )
    parser.add_argument(
        "--audiodev",
        dest="AUDIO_INPUT_DEVICE",
        default=-1,
        type=int,
        help="audio device number to use, use -2 to automatically select a loopback device",
    )
    parser.add_argument("--debug", dest="DEBUGGING_MODE", action="store_true")
    parser.add_argument(
        "--timeout",
        dest="TIMEOUT",
        default=30,
        type=int,
        help="Timeout (seconds) before test ends",
    )
    parser.add_argument(
        "--list",
        dest="LIST",
        action="store_true",
        help="list audio devices by number and exit",
    )

    args, _ = parser.parse_known_args()
    return args


if __name__ == "__main__":
    util_rx()
