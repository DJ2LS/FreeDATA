# File: arq_data_type_handler.py

import structlog
import lzma
import gzip
from message_p2p import message_received

class ARQDataTypeHandler:
    def __init__(self, event_manager):
        self.logger = structlog.get_logger(type(self).__name__)
        self.event_manager = event_manager
        self.handlers = {
            "raw": {
                'prepare': self.prepare_raw,
                'handle': self.handle_raw
            },
            "raw_lzma": {
                'prepare': self.prepare_raw_lzma,
                'handle': self.handle_raw_lzma
            },
            "raw_gzip": {
                'prepare': self.prepare_raw_gzip,
                'handle': self.handle_raw_gzip
            },
            "p2pmsg_lzma": {
                'prepare': self.prepare_p2pmsg_lzma,
                'handle': self.handle_p2pmsg_lzma
            },
        }

    def dispatch(self, type_byte: int, data: bytearray):
        endpoint_name = list(self.handlers.keys())[type_byte]
        if endpoint_name in self.handlers and 'handle' in self.handlers[endpoint_name]:
            return self.handlers[endpoint_name]['handle'](data)
        else:
            self.log(f"Unknown handling endpoint: {endpoint_name}", isWarning=True)

    def prepare(self, data: bytearray, endpoint_name="raw" ):
        if endpoint_name in self.handlers and 'prepare' in self.handlers[endpoint_name]:
            return self.handlers[endpoint_name]['prepare'](data), list(self.handlers.keys()).index(endpoint_name)
        else:
            self.log(f"Unknown preparation endpoint: {endpoint_name}", isWarning=True)

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

    def prepare_raw_lzma(self, data):
        compressed_data = lzma.compress(data)
        self.log(f"Preparing LZMA compressed data: {len(data)} Bytes >>> {len(compressed_data)} Bytes")
        return compressed_data

    def handle_raw_lzma(self, data):
        decompressed_data = lzma.decompress(data)
        self.log(f"Handling LZMA compressed data: {len(decompressed_data)} Bytes from {len(data)} Bytes")
        return decompressed_data

    def prepare_raw_gzip(self, data):
        compressed_data = gzip.compress(data)
        self.log(f"Preparing GZIP compressed data: {len(data)} Bytes >>> {len(compressed_data)} Bytes")
        return compressed_data

    def handle_raw_gzip(self, data):
        decompressed_data = gzip.decompress(data)
        self.log(f"Handling GZIP compressed data: {len(decompressed_data)} Bytes from {len(data)} Bytes")
        return decompressed_data

    def prepare_p2pmsg_lzma(self, data):
        compressed_data = lzma.compress(data)
        self.log(f"Preparing LZMA compressed P2PMSG data: {len(data)} Bytes >>> {len(compressed_data)} Bytes")
        return compressed_data

    def handle_p2pmsg_lzma(self, data):
        decompressed_data = lzma.decompress(data)
        self.log(f"Handling LZMA compressed P2PMSG data: {len(decompressed_data)} Bytes from {len(data)} Bytes")
        message_received(self.event_manager, decompressed_data)
        return decompressed_data
