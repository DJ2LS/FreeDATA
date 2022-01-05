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



PTT_STATE = False

HAMLIB_PTT_TYPE = 'RTS'
HAMLIB_DEVICE_NAME = 'RIG_MODEL_DUMMY_NOVFO'
HAMLIB_DEVICE_PORT = '/dev/ttyUSB0'
HAMLIB_SERIAL_SPEED = '9600'
HAMLIB_PTT_PORT = '/dev/ttyUSB0'
HAMLIB_STOP_BITS = '1'
HAMLIB_DATA_BITS = '8'
HAMLIB_HANDSHAKE = 'None'

HAMLIB_FREQUENCY = 0
HAMLIB_MODE = ''
HAMLIB_BANDWITH = 0
# -------------------------
# FreeDV Defaults

SNR = 0
FREQ_OFFSET = 0
SCATTER = []
# ---------------------------------

# Audio Defaults
AUDIO_INPUT_DEVICE = -2
AUDIO_OUTPUT_DEVICE = -2


AUDIO_RMS = 0
FFT = []



# ARQ statistics
ARQ_BYTES_PER_MINUTE_BURST = 0
ARQ_BYTES_PER_MINUTE = 0
ARQ_BITS_PER_SECOND_BURST = 0
ARQ_BITS_PER_SECOND = 0
ARQ_COMPRESSION_FACTOR = 0
ARQ_TRANSMISSION_PERCENT = 0
TOTAL_BYTES = 0


#CHANNEL_STATE = 'RECEIVING_SIGNALLING'
TNC_STATE = 'IDLE'
ARQ_STATE = False

# BEACON STATE
BEACON_STATE = False

# ------- RX BUFFER
RX_BUFFER = []
RX_MSG_BUFFER = []
RX_BURST_BUFFER = []
RX_FRAME_BUFFER = b''
#RX_BUFFER_SIZE = 0

# ------- HEARD STATIOS BUFFER
HEARD_STATIONS = []

# ------- INFO MESSAGE BUFFER
INFO = []
