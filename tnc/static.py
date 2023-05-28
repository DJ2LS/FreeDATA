#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 11:13:57 2020

@author: DJ2LS
Here we are saving application wide variables and stats, which have to be accessed everywhere.
"""

from dataclasses import dataclass, field
from typing import List
import subprocess
from enum import Enum


# CHANNEL_STATE = 'RECEIVING_SIGNALLING'
# disconnected, connecting, connected, disconnecting, failed
# ------- RX BUFFER

@dataclass 
class ARQ:
    bytes_per_minute: int = 0
    arq_transmission_percent: int = 0
    arq_compression_factor: int = 0
    arq_speed_level: int = 0
    arq_bits_per_second_burst: int = 0
    arq_bits_per_second: int = 0
    arq_seconds_until_finish: int = 0
    rx_buffer_size: int = 16
    rx_frame_buffer: bytes = b""
    rx_burst_buffer = []
    arq_session_state: str = "disconnected" # can be: disconnected, disconnecting, connected, connecting, failed
    arq_session: bool = False
    arq_state: bool = False
    # ARQ PROTOCOL VERSION
    # v.5 - signalling frame uses datac0
    # v.6 - signalling frame uses datac13
    arq_protocol_version: int = 6
    total_bytes: int = 0
    speed_list = []
    # set save to folder state for allowing downloading files to local file system
    arq_save_to_folder: bool = False
    bytes_per_minute_burst: int = 0
    rx_msg_buffer = []


@dataclass
class AudioParam:
    tx_audio_level: int = 50
    audio_input_devices = []
    audio_output_devices = []
    audio_input_device: int = -2
    audio_output_device: int = -2
    audio_record: bool = False
    audio_record_file = ''
    buffer_overflow_counter = [0, 0, 0, 0, 0]
    audio_auto_tune: bool = False
    # Audio TCI Support
    audio_enable_tci: bool = False
    audio_dbfs: int = 0
    fft = []
    enable_fft: bool = True


@dataclass
class Beacon:
    beacon_state: bool = False
    beacon_pause: bool = False

@dataclass 
class Channel:
    pass

@dataclass 
class Daemon:
    tncprocess: subprocess.Popen
    tncstarted: bool = False
    port: int = 3001
    serial_devices = []

@dataclass 
class HamlibParam:
    alc: int = 0
    hamlib_frequency: int = 0
    hamlib_strength: int = 0
    hamlib_radiocontrol: str = "disabled"
    hamlib_rigctld_ip: str = "127.0.0.1"
    hamlib_rigctld_port: str = "4532"
    ptt_state: bool = False
    hamlib_bandwidth: int = 0
    hamlib_status: str = "unknown/disconnected"
    hamlib_mode: str = ""
    hamlib_rf: int = 0

@dataclass
class MeshParam:
    routing_table = []
@dataclass
class ModemParam:
    tuning_range_fmin: float = -50.0
    tuning_range_fmax: float = 50.0
    channel_busy: bool = False
    channel_busy_slot = [False] * 5
    snr: float = 0
    is_codec2_traffic: bool = False  # true if we have codec2 signalling mode traffic on channel
    frequency_offset: float = 0
    tx_delay: int = 0  # delay in ms before sending modulation for triggering VOX for example or slow PTT radios
    enable_scatter: bool = False
    scatter = []

@dataclass
class Station:
    mycallsign: bytes = b"AA0AA"
    mycallsign_crc: bytes = b"A"
    dxcallsign: bytes = b"ZZ9YY"
    dxcallsign_crc: bytes = b"A"
    mygrid: bytes = b""
    dxgrid: bytes = b""
    ssid_list = []  # ssid list we are responding to


@dataclass
class Statistics:
    pass

@dataclass 
class TCIParam:
    ip: str = '127.0.0.1'
    port: int = '9000'

@dataclass 
class TNC:
    version = "0.10.0-alpha.1-mesh-exp3"
    host: str = "0.0.0.0"
    port: int = 3000
    SOCKET_TIMEOUT: int = 1  # seconds
    tnc_state: str = "IDLE"
    enable_explorer = False
    enable_stats = False
    transmitting: bool = False
    low_bandwidth_mode: bool = False
    enable_fsk: bool = False
    respond_to_cq: bool = True
    respond_to_call: bool = True  # respond to cq, ping, connection request, file request if not in session
    heard_stations = []
    listen: bool = True

    # ------------


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
    MESH_BROADCAST = 100
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
    FEC_WAKEUP = 252
    IDENT = 254
    TEST_FRAME = 255

# ---------------------------------------------------------------
# DON'T USE THESE SETTINGS ANYMORE
# ---------------------------------------------------------------
# Fixme: REMOVE THESE OLD SETTINGS!
# REASON: For some reason ctests are failing when using dataclasses.
# We need to figure out whats happening and why the tests are failing.


CHANNEL_BUSY_SLOT = [False] * 5


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
# CHECKED # ARQ_PROTOCOL_VERSION: int = 6

# ARQ statistics
# CHECKED # SPEED_LIST: list = []
# CHECKED # ARQ_BYTES_PER_MINUTE_BURST: int = 0
# CHECKED # ARQ_BYTES_PER_MINUTE: int = 0
# CHECKED # ARQ_BITS_PER_SECOND_BURST: int = 0
# CHECKED # ARQ_BITS_PER_SECOND: int = 0
# CHECKED # ARQ_COMPRESSION_FACTOR: int = 0
# CHECKED # ARQ_TRANSMISSION_PERCENT: int = 0
# CHECKED # ARQ_SECONDS_UNTIL_FINISH: int = 0
# CHECKED # ARQ_SPEED_LEVEL: int = 0
# CHECKED # TOTAL_BYTES: int = 0
# set save to folder state for allowing downloading files to local file system
# CHECKED # ARQ_SAVE_TO_FOLDER: bool = False

# CHANNEL_STATE = 'RECEIVING_SIGNALLING'
TNC_STATE: str = "IDLE"
# CHECKED # ARQ_STATE: bool = False
# CHECKED # ARQ_SESSION: bool = False
# disconnected, connecting, connected, disconnecting, failed
# CHECKED # ARQ_SESSION_STATE: str = "disconnected"

# BEACON STATE
BEACON_STATE: bool = False
BEACON_PAUSE: bool = False

# ------- RX BUFFER
# CHECKED # RX_MSG_BUFFER: list = []
# CHECKED # RX_BURST_BUFFER: list = []
# CHECKED # RX_FRAME_BUFFER: bytes = b""
# CHECKED # RX_BUFFER_SIZE: int = 16

# ------- HEARD STATIONS BUFFER
HEARD_STATIONS: list = []

# ------- CODEC2 SETTINGS
TUNING_RANGE_FMIN: float = -50.0
TUNING_RANGE_FMAX: float = 50.0
IS_CODEC2_TRAFFIC: bool = False  # true if we have codec2 signalling mode traffic on channel
