#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 11:13:57 2020

@author: DJ2LS
Here we are saving application wide variables and stats, which have to be accessed everywhere.
Not nice, tipps are appreciated :-) 
"""

# DAEMON
DAEMONPORT = 3001
TNCSTARTED = False
TNCPROCESS = 0


# Operator Defaults
MYCALLSIGN = b'AA0AA'
MYCALLSIGN_CRC8 = b'A'

DXCALLSIGN = b'AA0AA'
DXCALLSIGN_CRC8 = b'A'

MYGRID = b''
DXGRID = b''

# ---------------------------------

# Server Defaults
HOST = "0.0.0.0"
PORT = 3000
SOCKET_TIMEOUT = 3 # seconds
# ---------------------------------


HAMLIB_PTT_TYPE = 'RTS'
PTT_STATE = False

HAMLIB_DEVICE_ID = 0
HAMLIB_DEVICE_PORT = '/dev/ttyUSB0'
HAMLIB_SERIAL_SPEED = '9600'


HAMLIB_FREQUENCY = 0
HAMLIB_MODE = ''
HAMLIB_BANDWITH = 0
# -------------------------
# FreeDV Defaults

BER = 0
SNR = 0
SCATTER = []
# ---------------------------------

# Audio Defaults
AUDIO_INPUT_DEVICE = 1
AUDIO_OUTPUT_DEVICE = 1


AUDIO_RMS = 0
FFT = []



# ARQ statistics
ARQ_BYTES_PER_MINUTE_BURST = 0
ARQ_BYTES_PER_MINUTE = 0
ARQ_BITS_PER_SECOND_BURST = 0
ARQ_BITS_PER_SECOND = 0
ARQ_TRANSMISSION_PERCENT = 0
TOTAL_BYTES = 0

CHANNEL_STATE = 'RECEIVING_SIGNALLING'
TNC_STATE = 'IDLE'
ARQ_STATE = 'IDLE'


# ------- RX BUFFER
RX_BUFFER = []
RX_BURST_BUFFER = []
RX_FRAME_BUFFER = []
#RX_BUFFER_SIZE = 0

# ------- HEARD STATIOS BUFFER
HEARD_STATIONS = []
