# File: arq_data_type_handler.py

import structlog
import lzma
import gzip
from message_p2p import message_received, message_failed, message_transmitted
from enum import Enum

class ARQ_SESSION_TYPES(Enum):
    raw = 0
    raw_lzma = 10
    raw_gzip = 11
    p2pmsg_lzma = 20

class ARQDataTypeHandler:
    def __init__(self, event_manager, state_manager):
        self.logger = structlog.get_logger(type(self).__name__)
        self.event_manager = event_manager
        self.state_manager = state_manager

        self.handlers = {
            ARQ_SESSION_TYPES.raw: {
                'prepare': self.prepare_raw,
                'handle': self.handle_raw,
                'failed': self.failed_raw,
                'transmitted': self.transmitted_raw,
            },
            ARQ_SESSION_TYPES.raw_lzma: {
                'prepare': self.prepare_raw_lzma,
                'handle': self.handle_raw_lzma,
                'failed': self.failed_raw_lzma,
                'transmitted': self.transmitted_raw_lzma,
            },
            ARQ_SESSION_TYPES.raw_gzip: {
                'prepare': self.prepare_raw_gzip,
                'handle': self.handle_raw_gzip,
                'failed': self.failed_raw_gzip,
                'transmitted': self.transmitted_raw_gzip,
            },
            ARQ_SESSION_TYPES.p2pmsg_lzma: {
                'prepare': self.prepare_p2pmsg_lzma,
                'handle': self.handle_p2pmsg_lzma,
                'failed' : self.failed_p2pmsg_lzma,
                'transmitted': self.transmitted_p2pmsg_lzma,
            },
        }

    @staticmethod
    def get_session_type_from_value(value):
        for session_type in ARQ_SESSION_TYPES:
            if session_type.value == value:
                return session_type
        return None

    def dispatch(self, type_byte: int, data: bytearray):
        session_type = self.get_session_type_from_value(type_byte)
        if session_type and session_type in self.handlers and 'handle' in self.handlers[session_type]:
            return self.handlers[session_type]['handle'](data)
        else:
            self.log(f"Unknown handling endpoint for type: {type_byte}", isWarning=True)

    def failed(self, type_byte: int, data: bytearray):
        session_type = self.get_session_type_from_value(type_byte)
        if session_type in self.handlers and 'failed' in self.handlers[session_type]:
            return self.handlers[session_type]['failed'](data)
        else:
            self.log(f"Unknown handling endpoint: {session_type}", isWarning=True)

    def prepare(self, data: bytearray, session_type=ARQ_SESSION_TYPES.raw):
        if session_type in self.handlers and 'prepare' in self.handlers[session_type]:
            return self.handlers[session_type]['prepare'](data), session_type.value
        else:
            self.log(f"Unknown preparation endpoint: {session_type}", isWarning=True)

    def transmitted(self, type_byte: int, data: bytearray):
        session_type = self.get_session_type_from_value(type_byte)
        if session_type in self.handlers and 'transmitted' in self.handlers[session_type]:
            return self.handlers[session_type]['transmitted'](data)
        else:
            self.log(f"Unknown handling endpoint: {session_type}", isWarning=True)

    def log(self, message, isWarning=False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def prepare_raw(self, data):
        self.log(f"Preparing uncompressed data: {len(data)} Bytes")
        return data

    def handle_raw(self, data):
        self.log(f"Handling uncompressed data: {len(data)} Bytes")
        return data

    def failed_raw(self, data):
        return

    def transmitted_raw(self, data):
        return data

    def prepare_raw_lzma(self, data):
        compressed_data = lzma.compress(data)
        self.log(f"Preparing LZMA compressed data: {len(data)} Bytes >>> {len(compressed_data)} Bytes")
        return compressed_data

    def handle_raw_lzma(self, data):
        decompressed_data = lzma.decompress(data)
        self.log(f"Handling LZMA compressed data: {len(decompressed_data)} Bytes from {len(data)} Bytes")
        return decompressed_data

    def failed_raw_lzma(self, data):
        return

    def transmitted_raw_lzma(self, data):
        decompressed_data = lzma.decompress(data)
        return decompressed_data

    def prepare_raw_gzip(self, data):
        compressed_data = gzip.compress(data)
        self.log(f"Preparing GZIP compressed data: {len(data)} Bytes >>> {len(compressed_data)} Bytes")
        return compressed_data

    def handle_raw_gzip(self, data):
        decompressed_data = gzip.decompress(data)
        self.log(f"Handling GZIP compressed data: {len(decompressed_data)} Bytes from {len(data)} Bytes")
        return decompressed_data

    def failed_raw_gzip(self, data):
        return

    def transmitted_raw_gzip(self, data):
        decompressed_data = gzip.decompress(data)
        return decompressed_data

    def prepare_p2pmsg_lzma(self, data):
        compressed_data = lzma.compress(data)
        self.log(f"Preparing LZMA compressed P2PMSG data: {len(data)} Bytes >>> {len(compressed_data)} Bytes")
        return compressed_data

    def handle_p2pmsg_lzma(self, data):
        decompressed_data = lzma.decompress(data)
        self.log(f"Handling LZMA compressed P2PMSG data: {len(decompressed_data)} Bytes from {len(data)} Bytes")
        message_received(self.event_manager, self.state_manager, decompressed_data)
        return decompressed_data

    def failed_p2pmsg_lzma(self, data):
        decompressed_data = lzma.decompress(data)
        self.log(f"Handling failed LZMA compressed P2PMSG data: {len(decompressed_data)} Bytes from {len(data)} Bytes", isWarning=True)
        message_failed(self.event_manager, self.state_manager, decompressed_data)
        return decompressed_data

    def transmitted_p2pmsg_lzma(self, data):
        decompressed_data = lzma.decompress(data)
        message_transmitted(self.event_manager, self.state_manager, decompressed_data)
        return decompressed_data