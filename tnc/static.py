#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 11:13:57 2020

@author: DJ2LS
Here we are saving application wide variables and stats, which have to be accessed everywhere.
Not nice, suggestions are appreciated :-)
"""

import subprocess
from enum import Enum
CHANNEL_BUSY_SLOT = [False] * 5

VERSION = "0.9.0-alpha-exp.3"

ENABLE_EXPLORER = False
ENABLE_STATS = False


# DAEMON
DAEMONPORT: int = 3001
TNCSTARTED: bool = False
TNCPROCESS: subprocess.Popen

# Operator Defaults
MYCALLSIGN: bytes = b"AA0AA"
MYCALLSIGN_CRC: bytes = b"A"

DXCALLSIGN: bytes = b"ZZ9YY"
DXCALLSIGN_CRC: bytes = b"A"

MYGRID: bytes = b""
DXGRID: bytes = b""

SSID_LIST: list = []  # ssid list we are responding to

LOW_BANDWIDTH_MODE: bool = False
# ---------------------------------

# Server Defaults
HOST: str = "0.0.0.0"
PORT: int = 3000
SOCKET_TIMEOUT: int = 1  # seconds
# ---------------------------------
SERIAL_DEVICES: list = []
# ---------------------------------
LISTEN: bool = True
PTT_STATE: bool = False
TRANSMITTING: bool = False

HAMLIB_RADIOCONTROL: str = "disabled"
HAMLIB_RIGCTLD_IP: str = "127.0.0.1"
HAMLIB_RIGCTLD_PORT: str = "4532"

HAMLIB_STATUS: str = "unknown/disconnected"
HAMLIB_FREQUENCY: int = 0
HAMLIB_MODE: str = ""
HAMLIB_BANDWIDTH: int = 0
HAMLIB_RF: int = 0
HAMLIB_ALC: int = 0
HAMLIB_STRENGTH: int = 0
# -------------------------
# FreeDV Defaults

SNR: float = 0
FREQ_OFFSET: float = 0
SCATTER: list = []
ENABLE_SCATTER: bool = False
ENABLE_FSK: bool = False
RESPOND_TO_CQ: bool = False
RESPOND_TO_CALL: bool = True  # respond to cq, ping, connection request, file request if not in session
TX_DELAY: int = 0  # delay in ms before sending modulation for triggering VOX for example or slow PTT radios
# ---------------------------------

# Audio Defaults
TX_AUDIO_LEVEL: int = 50
AUDIO_INPUT_DEVICES: list = []
AUDIO_OUTPUT_DEVICES: list = []
AUDIO_INPUT_DEVICE: int = -2
AUDIO_OUTPUT_DEVICE: int = -2
AUDIO_RECORD: bool = False
AUDIO_RECORD_FILE = ''
BUFFER_OVERFLOW_COUNTER: list = [0, 0, 0, 0, 0]
AUDIO_AUTO_TUNE: bool = False
# Audio TCI Support
AUDIO_ENABLE_TCI: bool = False
TCI_IP: str = '127.0.0.1'
TCI_PORT: int = '9000'



AUDIO_DBFS: int = 0
FFT: list = [0]
ENABLE_FFT: bool = True
CHANNEL_BUSY: bool = False

# ARQ PROTOCOL VERSION
# v.5 - signalling frame uses datac0
# v.6 - signalling frame uses datac13
ARQ_PROTOCOL_VERSION: int = 6

# ARQ statistics
SPEED_LIST: list = []
ARQ_BYTES_PER_MINUTE_BURST: int = 0
ARQ_BYTES_PER_MINUTE: int = 0
ARQ_BITS_PER_SECOND_BURST: int = 0
ARQ_BITS_PER_SECOND: int = 0
ARQ_COMPRESSION_FACTOR: int = 0
ARQ_TRANSMISSION_PERCENT: int = 0
ARQ_SECONDS_UNTIL_FINISH: int = 0
ARQ_SPEED_LEVEL: int = 0
TOTAL_BYTES: int = 0
# set save to folder state for allowing downloading files to local file system
ARQ_SAVE_TO_FOLDER: bool = False

# CHANNEL_STATE = 'RECEIVING_SIGNALLING'
TNC_STATE: str = "IDLE"
ARQ_STATE: bool = False
ARQ_SESSION: bool = False
# disconnected, connecting, connected, disconnecting, failed
ARQ_SESSION_STATE: str = "disconnected"

# BEACON STATE
BEACON_STATE: bool = False
BEACON_PAUSE: bool = False

# ------- RX BUFFER
RX_MSG_BUFFER: list = []
RX_BURST_BUFFER: list = []
RX_FRAME_BUFFER: bytes = b""
RX_BUFFER_SIZE: int = 16

# ------- HEARD STATIONS BUFFER
HEARD_STATIONS: list = []

# ------- INFO MESSAGE BUFFER
# TODO: This can be removed?
INFO: list = []

# ------- CODEC2 SETTINGS
TUNING_RANGE_FMIN: float = -50.0
TUNING_RANGE_FMAX: float = 50.0
IS_CODEC2_TRAFFIC: bool = False # true if we have codec2 signalling mode traffic on channel

class FRAME_TYPE(Enum):
    """Lookup for frame types"""

    BURST_01 = 10
    BURST_02 = 11
    BURST_03 = 12
    BURST_04 = 13
    # ...
    BURST_51 = 50
    BURST_ACK = 60
    FR_ACK = 61
    FR_REPEAT = 62
    FR_NACK = 63
    BURST_NACK = 64
    CQ = 200
    QRV = 201
    PING = 210
    PING_ACK = 211
    IS_WRITING = 215
    ARQ_SESSION_OPEN = 221
    ARQ_SESSION_HB = 222
    ARQ_SESSION_CLOSE = 223
    ARQ_DC_OPEN_W = 225
    ARQ_DC_OPEN_ACK_W = 226
    ARQ_DC_OPEN_N = 227
    ARQ_DC_OPEN_ACK_N = 228
    ARQ_STOP = 249
    BEACON = 250
    FEC = 251
    IDENT = 254
    TEST_FRAME = 255
