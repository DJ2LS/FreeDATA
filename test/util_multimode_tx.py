#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send-side station emulator for test frame tests over a high quality audio channel
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

import numpy as np
import pyaudio

sys.path.insert(0, "..")
from tnc import codec2


def test_mm_tx():
    MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
    AUDIO_SAMPLE_RATE_TX = 48000
    assert (AUDIO_SAMPLE_RATE_TX % MODEM_SAMPLE_RATE) == 0

    args = parse_arguments()

    if args.LIST:
        p_audio = pyaudio.PyAudio()
        for dev in range(p_audio.get_device_count()):
            print("audiodev: ", dev, p_audio.get_device_info_by_index(dev)["name"])
        sys.exit()

    N_BURSTS = args.N_BURSTS
    N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
    DELAY_BETWEEN_BURSTS = args.DELAY_BETWEEN_BURSTS / 1000
    AUDIO_OUTPUT_DEVICE = args.AUDIO_OUTPUT_DEVICE

    resampler = codec2.resampler()

    # Data binary string
    data_out = b"HELLO WORLD!"

    modes = [
        codec2.api.FREEDV_MODE_DATAC0,
        codec2.api.FREEDV_MODE_DATAC1,
        codec2.api.FREEDV_MODE_DATAC3,
    ]

    if AUDIO_OUTPUT_DEVICE != -1:
        p_audio = pyaudio.PyAudio()
        # Auto search for loopback devices
        if AUDIO_OUTPUT_DEVICE == -2:
            loopback_list = [
                dev
                for dev in range(p_audio.get_device_count())
                if "Loopback: PCM" in p_audio.get_device_info_by_index(dev)["name"]
            ]

            if len(loopback_list) >= 2:
                AUDIO_OUTPUT_DEVICE = loopback_list[1]  # 0  = RX   1 = TX
                print(f"loopback_list tx: {loopback_list}", file=sys.stderr)
            else:
                sys.exit()

        # AUDIO PARAMETERS
        AUDIO_FRAMES_PER_BUFFER = 2400
        # pyaudio init
        stream_tx = p_audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=AUDIO_SAMPLE_RATE_TX,
            frames_per_buffer=AUDIO_FRAMES_PER_BUFFER,  # n_nom_modem_samples
            output=True,
            output_device_index=AUDIO_OUTPUT_DEVICE,
        )

    for mode in modes:
        freedv = ctypes.cast(codec2.api.freedv_open(mode), ctypes.c_void_p)

        n_tx_modem_samples = codec2.api.freedv_get_n_tx_modem_samples(freedv)
        mod_out = ctypes.create_string_buffer(2 * n_tx_modem_samples)

        n_tx_preamble_modem_samples = codec2.api.freedv_get_n_tx_preamble_modem_samples(
            freedv
        )
        mod_out_preamble = ctypes.create_string_buffer(2 * n_tx_preamble_modem_samples)

        n_tx_postamble_modem_samples = (
            codec2.api.freedv_get_n_tx_postamble_modem_samples(freedv)
        )
        mod_out_postamble = ctypes.create_string_buffer(
            2 * n_tx_postamble_modem_samples
        )

        bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(freedv) / 8)
        payload_per_frame = bytes_per_frame - 2

        buffer = bytearray(payload_per_frame)
        # Set buffer size to length of data which will be sent
        buffer[: len(data_out)] = data_out

        # Generate CRC16
        crc = ctypes.c_ushort(
            codec2.api.freedv_gen_crc16(bytes(buffer), payload_per_frame)
        )
        # Convert CRC to 2 byte hex string
        crc = crc.value.to_bytes(2, byteorder="big")
        buffer += crc  # Append crc16 to buffer
        data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)

        for brst in range(1, N_BURSTS + 1):
            # Write preamble to txbuffer
            codec2.api.freedv_rawdatapreambletx(freedv, mod_out_preamble)
            txbuffer = bytes(mod_out_preamble)

            # Create modulaton for N = FRAMESPERBURST and append it to txbuffer
            for frm in range(1, N_FRAMES_PER_BURST + 1):
                data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
                # Modulate DATA and save it into mod_out pointer
                codec2.api.freedv_rawdatatx(freedv, mod_out, data)

                txbuffer += bytes(mod_out)
                print(
                    f"TX BURST: {brst}/{N_BURSTS} FRAME: {frm}/{N_FRAMES_PER_BURST}",
                    file=sys.stderr,
                )

            # Append postamble to txbuffer
            codec2.api.freedv_rawdatapostambletx(freedv, mod_out_postamble)
            txbuffer += bytes(mod_out_postamble)

            # Append a delay between bursts as audio silence
            samples_delay = int(MODEM_SAMPLE_RATE * DELAY_BETWEEN_BURSTS)
            mod_out_silence = ctypes.create_string_buffer(samples_delay * 2)
            txbuffer += bytes(mod_out_silence)

            # Resample up to 48k (resampler works on np.int16)
            audio_buffer = np.frombuffer(txbuffer, dtype=np.int16)
            txbuffer_48k = resampler.resample8_to_48(audio_buffer)

            # Check if we want to use an audio device or stdout
            if AUDIO_OUTPUT_DEVICE != -1:
                stream_tx.write(txbuffer_48k.tobytes())
            else:
                # This test needs a lot of time, so we are having a look at times...
                starttime = time.time()

                # Print data to terminal for piping the output to other programs
                sys.stdout.buffer.write(txbuffer_48k)
                sys.stdout.flush()

                # and at least print the needed time to see which time we needed
                timeneeded = time.time() - starttime
                # print(f"time: {timeneeded} buffer: {len(txbuffer)}", file=sys.stderr)

    # and at last check if we had an opened pyaudio instance and close it
    if AUDIO_OUTPUT_DEVICE != -1:
        time.sleep(stream_tx.get_output_latency())
        stream_tx.stop_stream()
        stream_tx.close()
        p_audio.terminate()


def parse_arguments():
    # GET PARAMETER INPUTS
    parser = argparse.ArgumentParser(description="FreeDATA TEST")
    parser.add_argument("--bursts", dest="N_BURSTS", default=1, type=int)
    parser.add_argument(
        "--framesperburst", dest="N_FRAMES_PER_BURST", default=1, type=int
    )
    parser.add_argument("--delay", dest="DELAY_BETWEEN_BURSTS", default=500, type=int)
    parser.add_argument(
        "--audiodev",
        dest="AUDIO_OUTPUT_DEVICE",
        default=-1,
        type=int,
        help="audio output device number to use",
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
    test_mm_tx()
