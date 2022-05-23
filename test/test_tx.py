#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import ctypes
import sys

import numpy as np
import sounddevice as sd

sys.path.insert(0, "..")
from tnc import codec2


def test_tx():
    args = parse_arguments()

    if args.LIST:
        devices = sd.query_devices(device=None, kind=None)

        for index, device in enumerate(devices):
            print(f"{index} {device['name']}")
        sd._terminate()
        sys.exit()

    N_BURSTS = args.N_BURSTS
    N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST
    DELAY_BETWEEN_BURSTS = args.DELAY_BETWEEN_BURSTS / 1000
    AUDIO_OUTPUT_DEVICE = args.AUDIO_OUTPUT_DEVICE

    MODE = codec2.FREEDV_MODE[args.FREEDV_MODE].value

    # AUDIO PARAMETERS
    AUDIO_FRAMES_PER_BUFFER = 2400
    MODEM_SAMPLE_RATE = codec2.api.FREEDV_FS_8000
    AUDIO_SAMPLE_RATE_TX = 48000
    assert (AUDIO_SAMPLE_RATE_TX % MODEM_SAMPLE_RATE) == 0

    # check if we want to use an audio device then do an pyaudio init
    if AUDIO_OUTPUT_DEVICE != -1:
        # auto search for loopback devices
        if AUDIO_OUTPUT_DEVICE == -2:
            loopback_list = []

            devices = sd.query_devices(device=None, kind=None)

            for index, device in enumerate(devices):
                if "Loopback: PCM" in device["name"]:
                    print(index)
                    loopback_list.append(index)

            if loopback_list:
                # 0  = RX   1 = TX
                AUDIO_OUTPUT_DEVICE = loopback_list[-1]
                print(f"loopback_list tx: {loopback_list}", file=sys.stderr)
            else:
                print("not enough audio loopback devices ready...")
                print("you should wait about 30 seconds...")
                sd._terminate()
                sys.exit()
        print(f"AUDIO OUTPUT DEVICE: {AUDIO_OUTPUT_DEVICE}", file=sys.stderr)

        # audio stream init
        stream_tx = sd.RawStream(
            channels=1,
            dtype="int16",
            device=(0, AUDIO_OUTPUT_DEVICE),
            samplerate=AUDIO_SAMPLE_RATE_TX,
            blocksize=4800,
        )

    resampler = codec2.resampler()

    # data binary string
    if args.TESTFRAMES:
        data_out = bytearray(14)
        data_out[:1] = bytes([255])
        data_out[1:2] = bytes([1])
        data_out[2:] = b"HELLO WORLD"
    else:
        data_out = b"HELLO WORLD!"

    # ----------------------------------------------------------------

    # Open codec2 instance
    freedv = ctypes.cast(codec2.api.freedv_open(MODE), ctypes.c_void_p)

    # Get number of bytes per frame for mode
    bytes_per_frame = int(codec2.api.freedv_get_bits_per_modem_frame(freedv) / 8)
    payload_bytes_per_frame = bytes_per_frame - 2

    # Init buffer for data
    n_tx_modem_samples = codec2.api.freedv_get_n_tx_modem_samples(freedv)
    mod_out = ctypes.create_string_buffer(n_tx_modem_samples * 2)

    # Init buffer for preample
    n_tx_preamble_modem_samples = codec2.api.freedv_get_n_tx_preamble_modem_samples(
        freedv
    )
    mod_out_preamble = ctypes.create_string_buffer(n_tx_preamble_modem_samples * 2)

    # Init buffer for postamble
    n_tx_postamble_modem_samples = codec2.api.freedv_get_n_tx_postamble_modem_samples(
        freedv
    )
    mod_out_postamble = ctypes.create_string_buffer(n_tx_postamble_modem_samples * 2)

    # Create buffer for data
    #   Use this if CRC16 checksum is required (DATA1-3)
    buffer = bytearray(payload_bytes_per_frame)
    # set buffersize to length of data which will be send
    buffer[: len(data_out)] = data_out

    # Create CRC for data frame - we are using the CRC function shipped with codec2 to avoid
    # CRC algorithm incompatibilities
    # generate CRC16
    crc = ctypes.c_ushort(
        codec2.api.freedv_gen_crc16(bytes(buffer), payload_bytes_per_frame)
    )
    crc = crc.value.to_bytes(2, byteorder="big")  # convert crc to 2 byte hex string
    buffer += crc  # append crc16 to buffer

    print(
        f"TOTAL BURSTS: {N_BURSTS} TOTAL FRAMES_PER_BURST: {N_FRAMES_PER_BURST}",
        file=sys.stderr,
    )

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
        # print(f"samples_delay: {samples_delay} DELAY_BETWEEN_BURSTS: {DELAY_BETWEEN_BURSTS}", file=sys.stderr)

        # Resample up to 48k (resampler works on np.int16)
        np_buffer = np.frombuffer(txbuffer, dtype=np.int16)
        txbuffer_48k = resampler.resample8_to_48(np_buffer)

        # Check if we want to use an audio device or stdout
        if AUDIO_OUTPUT_DEVICE != -1:
            stream_tx.start()
            stream_tx.write(txbuffer_48k)
        else:
            # Print data to terminal for piping the output to other programs
            sys.stdout.buffer.write(txbuffer_48k)
            sys.stdout.flush()

    # and at last check if we had an opened audio instance and close it
    if AUDIO_OUTPUT_DEVICE != -1:
        sd._terminate()


def parse_arguments():
    # GET PARAMETER INPUTS
    parser = argparse.ArgumentParser(description="Simons TEST TNC")
    parser.add_argument("--bursts", dest="N_BURSTS", default=1, type=int)
    parser.add_argument(
        "--framesperburst", dest="N_FRAMES_PER_BURST", default=1, type=int
    )
    parser.add_argument(
        "--delay",
        dest="DELAY_BETWEEN_BURSTS",
        default=500,
        type=int,
        help="delay between bursts in ms",
    )
    parser.add_argument(
        "--mode", dest="FREEDV_MODE", type=str, choices=["datac0", "datac1", "datac3"]
    )
    parser.add_argument(
        "--audiodev",
        dest="AUDIO_OUTPUT_DEVICE",
        default=-1,
        type=int,
        help="audio output device number to use, use -2 to automatically select a loopback device",
    )
    parser.add_argument(
        "--list",
        dest="LIST",
        action="store_true",
        help="list audio devices by number and exit",
    )
    parser.add_argument(
        "--testframes",
        dest="TESTFRAMES",
        action="store_true",
        default=False,
        help="list audio devices by number and exit",
    )

    args, _ = parser.parse_known_args()
    return args


if __name__ == "__main__":
    test_tx()
