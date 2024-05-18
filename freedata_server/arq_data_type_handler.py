# File: arq_data_type_handler.py

import structlog
import lzma
import gzip
import zlib
from message_p2p import message_received, message_failed, message_transmitted
from enum import Enum

class ARQ_SESSION_TYPES(Enum):
    raw = 0
    raw_lzma = 10
    raw_gzip = 11
    p2pmsg_zlib = 20
    p2p_connection = 30

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
            ARQ_SESSION_TYPES.p2pmsg_zlib: {
                'prepare': self.prepare_p2pmsg_zlib,
                'handle': self.handle_p2pmsg_zlib,
                'failed' : self.failed_p2pmsg_zlib,
                'transmitted': self.transmitted_p2pmsg_zlib,
            },
            ARQ_SESSION_TYPES.p2p_connection: {
                'prepare': self.prepare_p2p_connection,
                'handle': self.handle_p2p_connection,
                'failed': self.failed_p2p_connection,
                'transmitted': self.transmitted_p2p_connection,
            },
        }

    @staticmethod
    def get_session_type_from_value(value):
        for session_type in ARQ_SESSION_TYPES:
            if session_type.value == value:
                return session_type
        return None

    def dispatch(self, type_byte: int, data: bytearray, statistics: dict):
        session_type = self.get_session_type_from_value(type_byte)

        self.state_manager.setARQ(False)

        if session_type and session_type in self.handlers and 'handle' in self.handlers[session_type]:
            return self.handlers[session_type]['handle'](data, statistics)
        else:
            self.log(f"Unknown handling endpoint for type: {type_byte}", isWarning=True)

    def failed(self, type_byte: int, data: bytearray, statistics: dict):
        session_type = self.get_session_type_from_value(type_byte)

        self.state_manager.setARQ(False)

        if session_type in self.handlers and 'failed' in self.handlers[session_type]:
            return self.handlers[session_type]['failed'](data, statistics)
        else:
            self.log(f"Unknown handling endpoint: {session_type}", isWarning=True)

    def prepare(self, data: bytearray, session_type=ARQ_SESSION_TYPES.raw):
        if session_type in self.handlers and 'prepare' in self.handlers[session_type]:
            return self.handlers[session_type]['prepare'](data), session_type.value
        else:
            self.log(f"Unknown preparation endpoint: {session_type}", isWarning=True)

    def transmitted(self, type_byte: int, data: bytearray, statistics: dict):
        session_type = self.get_session_type_from_value(type_byte)

        self.state_manager.setARQ(False)

        if session_type in self.handlers and 'transmitted' in self.handlers[session_type]:
            return self.handlers[session_type]['transmitted'](data, statistics)
        else:
            self.log(f"Unknown handling endpoint: {session_type}", isWarning=True)

    def log(self, message, isWarning=False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def prepare_raw(self, data):
        self.log(f"Preparing uncompressed data: {len(data)} Bytes")
        return data

    def handle_raw(self, data, statistics):
        self.log(f"Handling uncompressed data: {len(data)} Bytes")
        return data

    def failed_raw(self, data, statistics):
        return

    def transmitted_raw(self, data, statistics):
        return data

    def prepare_raw_lzma(self, data):
        compressed_data = lzma.compress(data)
        self.log(f"Preparing LZMA compressed data: {len(data)} Bytes >>> {len(compressed_data)} Bytes")
        return compressed_data

    def handle_raw_lzma(self, data, statistics):
        decompressed_data = lzma.decompress(data)
        self.log(f"Handling LZMA compressed data: {len(decompressed_data)} Bytes from {len(data)} Bytes")
        return decompressed_data

    def failed_raw_lzma(self, data, statistics):
        return

    def transmitted_raw_lzma(self, data, statistics):
        decompressed_data = lzma.decompress(data)
        return decompressed_data

    def prepare_raw_gzip(self, data):
        compressed_data = gzip.compress(data)
        self.log(f"Preparing GZIP compressed data: {len(data)} Bytes >>> {len(compressed_data)} Bytes")
        return compressed_data

    def handle_raw_gzip(self, data, statistics):
        decompressed_data = gzip.decompress(data)
        self.log(f"Handling GZIP compressed data: {len(decompressed_data)} Bytes from {len(data)} Bytes")
        return decompressed_data

    def failed_raw_gzip(self, data, statistics):
        return

    def transmitted_raw_gzip(self, data, statistics):
        decompressed_data = gzip.decompress(data)
        return decompressed_data

    def prepare_p2pmsg_zlib(self, data):
        compressed_data = lzma.compress(data)

        compressor = zlib.compressobj(level=6, wbits=-zlib.MAX_WBITS, strategy=zlib.Z_FILTERED)
        compressed_data = compressor.compress(data) + compressor.flush()

        self.log(f"Preparing ZLIB compressed P2PMSG data: {len(data)} Bytes >>> {len(compressed_data)} Bytes")
        return compressed_data

    def handle_p2pmsg_zlib(self, data, statistics):
        decompressor = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        decompressed_data = decompressor.decompress(data)
        decompressed_data += decompressor.flush()

        self.log(f"Handling ZLIB compressed P2PMSG data: {len(decompressed_data)} Bytes from {len(data)} Bytes")
        message_received(self.event_manager, self.state_manager, decompressed_data, statistics)
        return decompressed_data

    def failed_p2pmsg_zlib(self, data, statistics):
        decompressor = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        decompressed_data = decompressor.decompress(data)
        decompressed_data += decompressor.flush()

        self.log(f"Handling failed ZLIB compressed P2PMSG data: {len(decompressed_data)} Bytes from {len(data)} Bytes", isWarning=True)
        message_failed(self.event_manager, self.state_manager, decompressed_data, statistics)
        return decompressed_data

    def transmitted_p2pmsg_zlib(self, data, statistics):
        # Create a decompression object with the same wbits setting used for compression
        decompressor = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        decompressed_data = decompressor.decompress(data)
        decompressed_data += decompressor.flush()

        message_transmitted(self.event_manager, self.state_manager, decompressed_data, statistics)
        return decompressed_data
    
    
    def prepare_p2p_connection(self, data):
        compressed_data = gzip.compress(data)
        self.log(f"Preparing gzip compressed P2P_CONNECTION data: {len(data)} Bytes >>> {len(compressed_data)} Bytes")
        print(self.state_manager.p2p_connection_sessions)
        return compressed_data

    def handle_p2p_connection(self, data, statistics):
        decompressed_data = gzip.decompress(data)
        self.log(f"Handling gzip compressed P2P_CONNECTION data: {len(decompressed_data)} Bytes from {len(data)} Bytes")
        print(self.state_manager.p2p_connection_sessions)
        print(decompressed_data)
        print(self.state_manager.p2p_connection_sessions)
        for session_id in self.state_manager.p2p_connection_sessions:
            print(session_id)
            self.state_manager.p2p_connection_sessions[session_id].received_arq(decompressed_data)

    def failed_p2p_connection(self, data, statistics):
        decompressed_data = gzip.decompress(data)
        self.log(f"Handling failed gzip compressed P2P_CONNECTION data: {len(decompressed_data)} Bytes from {len(data)} Bytes", isWarning=True)
        print(self.state_manager.p2p_connection_sessions)
        return decompressed_data

    def transmitted_p2p_connection(self, data, statistics):

        decompressed_data = gzip.decompress(data)
        print(decompressed_data)
        print(self.state_manager.p2p_connection_sessions)
        for session_id in self.state_manager.p2p_connection_sessions:
            print(session_id)
            self.state_manager.p2p_connection_sessions[session_id].transmitted_arq()