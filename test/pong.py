#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

import ctypes
from ctypes import *
import pathlib
import pyaudio
import sys
import logging
import time
import threading
import sys
import argparse

#--------------------------------------------GET PARAMETER INPUTS
parser = argparse.ArgumentParser(description='Simons TEST TNC')
parser.add_argument('--bursts', dest="N_BURSTS", default=0, type=int)
parser.add_argument('--frames', dest="N_FRAMES_PER_BURST", default=0, type=int)
parser.add_argument('--txmode', dest="FREEDV_TX_MODE", default=0, type=int)
parser.add_argument('--rxmode', dest="FREEDV_RX_MODE", default=0, type=int)
parser.add_argument('--audioinput', dest="AUDIO_INPUT", default=0, type=int)
parser.add_argument('--audiooutput', dest="AUDIO_OUTPUT", default=0, type=int)
parser.add_argument('--debug', dest="DEBUGGING_MODE", action="store_true")

args, _ = parser.parse_known_args()

N_BURSTS = args.N_BURSTS
N_FRAMES_PER_BURST = args.N_FRAMES_PER_BURST

AUDIO_OUTPUT_DEVICE = args.AUDIO_OUTPUT
AUDIO_INPUT_DEVICE = args.AUDIO_INPUT

FREEDV_TX_MODE = args.FREEDV_TX_MODE
FREEDV_RX_MODE = args.FREEDV_RX_MODE

DEBUGGING_MODE = args.DEBUGGING_MODE

# 1024 good for mode 6
AUDIO_FRAMES_PER_BUFFER = 2048
MODEM_SAMPLE_RATE = 8000

        #-------------------------------------------- LOAD FREEDV
libname = pathlib.Path().absolute() / "codec2/build_linux/src/libcodec2.so"
c_lib = ctypes.CDLL(libname)
     #--------------------------------------------CREATE PYAUDIO  INSTANCE
p = pyaudio.PyAudio()
        #--------------------------------------------GET SUPPORTED SAMPLE RATES FROM SOUND DEVICE

#AUDIO_SAMPLE_RATE_TX = int(p.get_device_info_by_index(AUDIO_OUTPUT_DEVICE)['defaultSampleRate'])
#AUDIO_SAMPLE_RATE_RX = int(p.get_device_info_by_index(AUDIO_INPUT_DEVICE)['defaultSampleRate'])
AUDIO_SAMPLE_RATE_TX = 8000
AUDIO_SAMPLE_RATE_RX = 8000
        #--------------------------------------------OPEN AUDIO CHANNEL RX

stream_tx = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=AUDIO_SAMPLE_RATE_TX,
                            frames_per_buffer=AUDIO_FRAMES_PER_BUFFER, #n_nom_modem_samples
                            output=True,
                            output_device_index=AUDIO_OUTPUT_DEVICE,
                            )

stream_rx = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=AUDIO_SAMPLE_RATE_RX,
                            frames_per_buffer=AUDIO_FRAMES_PER_BUFFER,
                            input=True,
                            input_device_index=AUDIO_INPUT_DEVICE,
                            )


    # GENERAL PARAMETERS
c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)


def send_pong(burst,n_total_burst,frame,n_total_frame):

    data_out = bytearray()
    data_out[0:1] = bytes([burst])
    data_out[1:2] = bytes([n_total_burst])
    data_out[2:3] = bytes([frame])
    data_out[4:5] = bytes([n_total_frame])



    c_lib.freedv_open.restype = ctypes.POINTER(ctypes.c_ubyte)
    freedv = c_lib.freedv_open(FREEDV_TX_MODE)
    bytes_per_frame = int(c_lib.freedv_get_bits_per_modem_frame(freedv)/8)
    payload_per_frame = bytes_per_frame -2
    n_nom_modem_samples = c_lib.freedv_get_n_nom_modem_samples(freedv)
    n_tx_modem_samples = c_lib.freedv_get_n_tx_modem_samples(freedv) #get n_tx_modem_samples which defines the size of the modulation object # --> *2

    mod_out = ctypes.c_short * n_tx_modem_samples
    mod_out = mod_out()
    mod_out_preamble = ctypes.c_short * (1760*2) #1760 for mode 10,11,12 #4000 for mode 9
    mod_out_preamble = mod_out_preamble()

    buffer = bytearray(payload_per_frame) # use this if CRC16 checksum is required ( DATA1-3)
    buffer[:len(data_out)] = data_out # set buffersize to length of data which will be send

    crc = ctypes.c_ushort(c_lib.freedv_gen_crc16(bytes(buffer), payload_per_frame))     # generate CRC16
    crc = crc.value.to_bytes(2, byteorder='big') # convert crc to 2 byte hex string
    buffer += crc        # append crc16 to buffer

    c_lib.freedv_rawdatapreambletx(freedv, mod_out_preamble);
    txbuffer = bytearray()
    txbuffer += bytes(mod_out_preamble)

    data = (ctypes.c_ubyte * bytes_per_frame).from_buffer_copy(buffer)
    c_lib.freedv_rawdatatx(freedv,mod_out,data) # modulate DATA and safe it into mod_out pointer

    txbuffer += bytes(mod_out)
    stream_tx.write(bytes(txbuffer))

    txbuffer = bytearray()



     # DATA CHANNEL INITIALISATION

freedv = c_lib.freedv_open(FREEDV_RX_MODE)
bytes_per_frame = int(c_lib.freedv_get_bits_per_modem_frame(freedv)/8)
n_max_modem_samples = c_lib.freedv_get_n_max_modem_samples(freedv)
bytes_out = (ctypes.c_ubyte * bytes_per_frame) #bytes_per_frame
bytes_out = bytes_out() #get pointer from bytes_out



receive = True
while receive == True:
    time.sleep(0.01)

    data_in = b''

    nin = c_lib.freedv_nin(freedv)
    nin_converted = int(nin*(AUDIO_SAMPLE_RATE_RX/MODEM_SAMPLE_RATE))
    if DEBUGGING_MODE == True:
        print("-----------------------------")
        print("NIN:  " + str(nin) + " [ " + str(nin_converted) + " ]")

    data_in = stream_rx.read(nin_converted,  exception_on_overflow = False)
    data_in = data_in.rstrip(b'\x00')

    c_lib.freedv_rawdatarx.argtype = [ctypes.POINTER(ctypes.c_ubyte), bytes_out, data_in] # check if really neccessary
    nbytes = c_lib.freedv_rawdatarx(freedv, bytes_out, data_in) # demodulate audio

    if DEBUGGING_MODE == True:
        print("SYNC: " + str(c_lib.freedv_get_rx_status(freedv)))

    if nbytes == bytes_per_frame:

            burst = bytes_out[0]
            n_total_burst = bytes_out[1]
            frame = bytes_out[2]
            n_total_frame = bytes_out[3]
            print("RX | BURST [" + str(burst) + "/" + str(n_total_burst) +  "] FRAME [" + str(frame) + "/" + str(n_total_frame) + "] >>> SENDING PONG")

            TRANSMIT_PONG = threading.Thread(target=send_pong, args=[burst,n_total_burst,frame,n_total_frame], name="SEND PONG")
            TRANSMIT_PONG.start()

            c_lib.freedv_set_sync(freedv,0)
