#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from enum import Enum


class FRAME_TYPE(Enum):
    """Lookup for frame types"""

    BURST_FRAME = 10
    BURST_ACK = 11
    BURST_NACK = 12
    FR_ACK = 61
    FR_REPEAT = 62
    FR_NACK = 63
    MESH_BROADCAST = 100
    MESH_SIGNALLING_PING = 101
    MESH_SIGNALLING_PING_ACK = 102
    CQ = 200
    QRV = 201
    PING = 210
    PING_ACK = 211
    IS_WRITING = 215
    ARQ_CONNECTION_OPEN = 221
    ARQ_CONNECTION_HB = 222
    ARQ_CONNECTION_CLOSE = 223
    ARQ_SESSION_OPEN = 225
    ARQ_SESSION_OPEN_ACK = 226
    ARQ_SESSION_INFO = 227
    ARQ_SESSION_INFO_ACK = 228
    ARQ_STOP = 249
    BEACON = 250
    FEC = 251
    FEC_WAKEUP = 252
    IDENT = 254
    TEST_FRAME = 255
