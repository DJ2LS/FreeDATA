#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 11:13:57 2020

@author: DJ2LS
Here we are saving application wide variables and stats, which have to be accessed everywhere.
Not nice, suggestions are appreciated :-)
"""

VERSION = "0.4.0-alpha"

# DAEMON
DAEMONPORT = 3001
TNCSTARTED = False
TNCPROCESS = 0

# Operator Defaults
MYCALLSIGN = b"AA0AA"
MYCALLSIGN_CRC = b"A"

DXCALLSIGN = b"AA0AA"
DXCALLSIGN_CRC = b"A"

MYGRID = b""
DXGRID = b""

SSID_LIST = []  # ssid list we are responding to

LOW_BANDWITH_MODE = False
# ---------------------------------

# Server Defaults
HOST = "0.0.0.0"
PORT = 3000
SOCKET_TIMEOUT = 1  # seconds
# ---------------------------------
SERIAL_DEVICES = []
# ---------------------------------

PTT_STATE = False
TRANSMITTING = False

HAMLIB_VERSION = "0"
HAMLIB_PTT_TYPE = "RTS"
HAMLIB_DEVICE_NAME = "RIG_MODEL_DUMMY_NOVFO"
HAMLIB_DEVICE_PORT = "/dev/ttyUSB0"
HAMLIB_SERIAL_SPEED = "9600"
HAMLIB_PTT_PORT = "/dev/ttyUSB0"
HAMLIB_STOP_BITS = "1"
HAMLIB_DATA_BITS = "8"
HAMLIB_HANDSHAKE = "None"
HAMLIB_RADIOCONTROL = "direct"
HAMLIB_RIGCTLD_IP = "127.0.0.1"
HAMLIB_RIGCTLD_PORT = "4532"

HAMLIB_FREQUENCY = 0
HAMLIB_MODE = ""
HAMLIB_BANDWITH = 0
# -------------------------
# FreeDV Defaults

SNR = 0
FREQ_OFFSET = 0
SCATTER = []
ENABLE_SCATTER = False
ENABLE_FSK = False
RESPOND_TO_CQ = False
# ---------------------------------

# Audio Defaults
TX_AUDIO_LEVEL = 50
AUDIO_INPUT_DEVICES = []
AUDIO_OUTPUT_DEVICES = []
AUDIO_INPUT_DEVICE = -2
AUDIO_OUTPUT_DEVICE = -2
BUFFER_OVERFLOW_COUNTER = [0, 0, 0, 0, 0]

AUDIO_RMS = 0
FFT = [0]
ENABLE_FFT = False
CHANNEL_BUSY = None

# ARQ PROTOCOL VERSION
ARQ_PROTOCOL_VERSION = 1

# ARQ statistics
ARQ_BYTES_PER_MINUTE_BURST = 0
ARQ_BYTES_PER_MINUTE = 0
ARQ_BITS_PER_SECOND_BURST = 0
ARQ_BITS_PER_SECOND = 0
ARQ_COMPRESSION_FACTOR = 0
ARQ_TRANSMISSION_PERCENT = 0
ARQ_SPEED_LEVEL = 0
TOTAL_BYTES = 0

# CHANNEL_STATE = 'RECEIVING_SIGNALLING'
TNC_STATE = "IDLE"
ARQ_STATE = False
ARQ_SESSION = False
ARQ_SESSION_STATE = "disconnected"  # disconnected, connecting, connected, disconnecting, failed

# BEACON STATE
BEACON_STATE = False
BEACON_PAUSE = False

# ------- RX BUFFER
RX_BUFFER = []
RX_MSG_BUFFER = []
RX_BURST_BUFFER = []
RX_FRAME_BUFFER = b""
# RX_BUFFER_SIZE = 0

# ------- HEARD STATIONS BUFFER
HEARD_STATIONS = []

# ------- INFO MESSAGE BUFFER
INFO = []

# ------- CODEC2 SETTINGS
TUNING_RANGE_FMIN = -50.0
TUNING_RANGE_FMAX = 50.0
