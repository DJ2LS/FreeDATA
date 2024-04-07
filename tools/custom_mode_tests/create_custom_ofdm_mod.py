"""

FreeDATA % python3.11 tools/custom_mode_tests/create_custom_ofdm_mod.py | ./modem/lib/codec2/build_osx/src/freedv_data_raw_rx --vv --framesperburst 1 DATAC1 - /dev/null


"""
import sys
sys.path.append('modem')
import numpy as np

modem_path = '/../../modem'
if modem_path not in sys.path:
    sys.path.append(modem_path)



#import modem.codec2 as codec2
from codec2 import *

import modulator as modulator
import config as config

config = config.CONFIG('config.ini')
modulator = modulator.Modulator(config.read())
#freedv = open_instance(FREEDV_MODE.data_ofdm_2438.value)
#freedv = open_instance(FREEDV_MODE.datac14.value)
#freedv = open_instance(FREEDV_MODE.datac1.value)
freedv = open_instance(FREEDV_MODE.datac3.value)
#freedv = open_instance(FREEDV_MODE.data_ofdm_500.value)
#freedv = open_instance(FREEDV_MODE.qam16c2.value)


frames = 1
txbuffer = bytearray()

for frame in range(0,frames):
    #txbuffer = modulator.transmit_add_silence(txbuffer, 1000)
    txbuffer = modulator.transmit_add_preamble(txbuffer, freedv)
    txbuffer = modulator.transmit_create_frame(txbuffer, freedv, b'123')
    txbuffer = modulator.transmit_add_postamble(txbuffer, freedv)
    txbuffer = modulator.transmit_add_silence(txbuffer, 1000)

sys.stdout.buffer.flush()
sys.stdout.buffer.write(txbuffer)
sys.stdout.buffer.flush()
