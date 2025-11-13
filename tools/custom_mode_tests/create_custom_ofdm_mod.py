"""

FreeDATA % python3.11 tools/custom_mode_tests/create_custom_ofdm_mod.py | ./freedata_server/lib/codec2/build_osx/src/freedv_data_raw_rx --vv --framesperburst 1 DATAC1 - /dev/null


"""

import sys

sys.path.append("freedata_server")
import numpy as np

modem_path = "/../../freedata_server"
if modem_path not in sys.path:
    sys.path.append(modem_path)


# import freedata_server.codec2 as codec2
from codec2 import *
import threading
import modulator as modulator
import demodulator as demodulator
import config as config

MODE = FREEDV_MODE.datac1


def demod(txbuffer):
    c2instance = open_instance(MODE.value)
    print(f"DEMOD: {MODE}")
    # get bytes per frame
    bytes_per_frame = int(api.freedv_get_bits_per_modem_frame(c2instance) / 8)
    # create byte out buffer
    bytes_out = ctypes.create_string_buffer(bytes_per_frame)

    # set initial frames per burst
    api.freedv_set_frames_per_burst(c2instance, 1)

    # init audio buffer
    audiobuffer = audio_buffer(len(txbuffer))

    # get initial nin
    nin = api.freedv_nin(c2instance)
    audiobuffer.push(txbuffer)
    threading.Event().wait(0.01)

    while audiobuffer.nbuffer >= nin:
        # demodulate audio
        nbytes = api.freedv_rawdatarx(freedv, bytes_out, audiobuffer.buffer.ctypes)
        # get current freedata_server states and write to list
        # 1 trial
        # 2 sync
        # 3 trial sync
        # 6 decoded
        # 10 error decoding == NACK
        rx_status = api.freedv_get_rx_status(freedv)
        # print(rx_status)

        # decrement codec traffic counter for making state smoother

        audiobuffer.pop(nin)
        nin = api.freedv_nin(freedv)
        if nbytes == bytes_per_frame:
            print("DECODED!!!!")

    print("---------------------------------")
    print("ENDED")
    print(nin)
    print(audiobuffer.nbuffer)


config = config.CONFIG("config.ini")
modulator = modulator.Modulator(config.read())
# freedv = open_instance(FREEDV_MODE.data_ofdm_2438.value)
# freedv = open_instance(FREEDV_MODE.datac14.value)
# freedv = open_instance(FREEDV_MODE.datac1.value)
freedv = open_instance(MODE.value)
print(f"MODULATE: {MODE}")
# freedv = open_instance(FREEDV_MODE.data_ofdm_500.value)
# freedv = open_instance(FREEDV_MODE.qam16c2.value)


frames = 1
txbuffer = bytearray()

for frame in range(0, frames):
    # txbuffer = modulator.transmit_add_silence(txbuffer, 1000)
    txbuffer = modulator.transmit_add_preamble(txbuffer, freedv)
    txbuffer = modulator.transmit_create_frame(txbuffer, freedv, b"123")
    txbuffer = modulator.transmit_add_postamble(txbuffer, freedv)
    txbuffer = modulator.transmit_add_silence(txbuffer, 1000)

# sys.stdout.buffer.flush()
# sys.stdout.buffer.write(txbuffer)
# sys.stdout.buffer.flush()
demod(txbuffer)
