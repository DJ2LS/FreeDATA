#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 11:13:57 2020

@author: DJ2LS
Here we are saving application wide variables and stats, which have to be accessed everywhere.
Not nice, suggestions are appreciated :-)
"""

import subprocess

VERSION = "0.4.2-alpha"

# DAEMON
DAEMONPORT: int = 3001
TNCSTARTED: bool = False
TNCPROCESS: subprocess.Popen

# Operator Defaults
MYCALLSIGN: bytes = b"AA0AA"
MYCALLSIGN_CRC: bytes = b"A"

DXCALLSIGN: bytes = b"AA0AA"
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

PTT_STATE: bool = False
TRANSMITTING: bool = False

HAMLIB_VERSION: str = "0"
HAMLIB_PTT_TYPE: str = "RTS"
HAMLIB_DEVICE_NAME: str = "RIG_MODEL_DUMMY_NOVFO"
HAMLIB_DEVICE_PORT: str = "/dev/ttyUSB0"
HAMLIB_SERIAL_SPEED: str = "9600"
HAMLIB_PTT_PORT: str = "/dev/ttyUSB0"
HAMLIB_STOP_BITS: str = "1"
HAMLIB_DATA_BITS: str = "8"
HAMLIB_HANDSHAKE: str = "None"
HAMLIB_RADIOCONTROL: str = "direct"
HAMLIB_RIGCTLD_IP: str = "127.0.0.1"
HAMLIB_RIGCTLD_PORT: str = "4532"

HAMLIB_FREQUENCY: int = 0
HAMLIB_MODE: str = ""
HAMLIB_BANDWIDTH: int = 0
# -------------------------
# FreeDV Defaults

SNR: float = 0
FREQ_OFFSET: float = 0
SCATTER: list = []
ENABLE_SCATTER: bool = False
ENABLE_FSK: bool = False
RESPOND_TO_CQ: bool = False
# ---------------------------------

# Audio Defaults
TX_AUDIO_LEVEL: int = 50
AUDIO_INPUT_DEVICES: list = []
AUDIO_OUTPUT_DEVICES: list = []
AUDIO_INPUT_DEVICE: int = -2
AUDIO_OUTPUT_DEVICE: int = -2
BUFFER_OVERFLOW_COUNTER: list = [0, 0, 0, 0, 0]

AUDIO_RMS: int = 0
FFT: list = [0]
ENABLE_FFT: bool = False
CHANNEL_BUSY: bool = False

# ARQ PROTOCOL VERSION
ARQ_PROTOCOL_VERSION: int = 1

# ARQ statistics
ARQ_BYTES_PER_MINUTE_BURST: int = 0
ARQ_BYTES_PER_MINUTE: int = 0
ARQ_BITS_PER_SECOND_BURST: int = 0
ARQ_BITS_PER_SECOND: int = 0
ARQ_COMPRESSION_FACTOR: int = 0
ARQ_TRANSMISSION_PERCENT: int = 0
ARQ_SPEED_LEVEL: int = 0
TOTAL_BYTES: int = 0

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
RX_BUFFER: list = []
RX_MSG_BUFFER: list = []
RX_BURST_BUFFER: list = []
RX_FRAME_BUFFER: bytes = b""
# RX_BUFFER_SIZE: int = 0

# ------- HEARD STATIONS BUFFER
HEARD_STATIONS: list = []

# ------- INFO MESSAGE BUFFER
INFO: list = []

# ------- CODEC2 SETTINGS
TUNING_RANGE_FMIN: float = -50.0
TUNING_RANGE_FMAX: float = 50.0
