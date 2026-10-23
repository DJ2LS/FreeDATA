"""
This module implements the ARQDataTypeHandler class, which is responsible for
preparing, handling, and processing different types of ARQ session data within the FreeData system.
It supports various session types (raw, compressed, and p2p-related) defined in the ARQ_SESSION_TYPES enumeration,
and routes data to the appropriate methods for compression, decompression, and event handling.
"""

import structlog
import lzma
import gzip
import zlib
from freedata_server import encryption
from freedata_server.message_p2p import (
    message_received,
    message_failed,
    message_transmitted,
    encrypted_message_received,
    decompress_p2pmsg,
)
from enum import Enum


class ARQ_SESSION_TYPES(Enum):
    """Enumeration for ARQ session types.

    This class defines various session types used in the ARQ protocol,
    each associated with a unique integer value. These session types
    help in identifying the format and compression method of the data
    being transmitted in ARQ communications.
    """

    raw = 0
    raw_lzma = 10
    raw_gzip = 11
    p2pmsg_zlib = 20
    p2pmsg_zlib_aesgcm = 21  # zlib compressed, then AES-256-GCM encrypted (encryption.py)
    p2p_connection = 30


class ARQDataTypeHandler:
    def __init__(self, ctx):
        self.logger = structlog.get_logger(type(self).__name__)

        self.ctx = ctx

        self.handlers = {
            ARQ_SESSION_TYPES.raw: {
                "prepare": self.prepare_raw,
                "handle": self.handle_raw,
                "failed": self.failed_raw,
                "transmitted": self.transmitted_raw,
            },
            ARQ_SESSION_TYPES.raw_lzma: {
                "prepare": self.prepare_raw_lzma,
                "handle": self.handle_raw_lzma,
                "failed": self.failed_raw_lzma,
                "transmitted": self.transmitted_raw_lzma,
            },
            ARQ_SESSION_TYPES.raw_gzip: {
                "prepare": self.prepare_raw_gzip,
                "handle": self.handle_raw_gzip,
                "failed": self.failed_raw_gzip,
                "transmitted": self.transmitted_raw_gzip,
            },
            ARQ_SESSION_TYPES.p2pmsg_zlib: {
                "prepare": self.prepare_p2pmsg_zlib,
                "handle": self.handle_p2pmsg_zlib,
                "failed": self.failed_p2pmsg_zlib,
                "transmitted": self.transmitted_p2pmsg_zlib,
            },
            ARQ_SESSION_TYPES.p2pmsg_zlib_aesgcm: {
                "prepare": self.prepare_p2pmsg_zlib_aesgcm,
                "handle": self.handle_p2pmsg_zlib_aesgcm,
                "failed": self.failed_p2pmsg_zlib_aesgcm,
                "transmitted": self.transmitted_p2pmsg_zlib_aesgcm,
            },
            ARQ_SESSION_TYPES.p2p_connection: {
                "prepare": self.prepare_p2p_connection,
                "handle": self.handle_p2p_connection,
                "failed": self.failed_p2p_connection,
                "transmitted": self.transmitted_p2p_connection,
            },
        }

    @staticmethod
    def get_session_type_from_value(value):
        """Retrieves the ARQ session type corresponding to the given value.

        This method iterates through the available ARQ session types and
        returns the matching type if the provided value equals the type's value.
        If no match is found, it returns None.

        Args:
            value: The integer value representing the ARQ session type.

        Returns:
            The corresponding ARQ_SESSION_TYPES enum member, or None if no match is found.
        """
        for session_type in ARQ_SESSION_TYPES:
            if session_type.value == value:
                return session_type
        return None

    def call_handler(self, session_type, action, data, statistics, session_id=None, dxcall=None):
        """Calls a registered handler function.

        P2P connection handlers additionally get the ARQ session id, which is
        equal to the id of the owning P2P connection session. Encrypted message
        handlers get the callsign of the remote station to look up its key.
        """
        handler = self.handlers[session_type][action]
        if session_type is ARQ_SESSION_TYPES.p2p_connection:
            return handler(data, statistics, session_id=session_id)
        if session_type is ARQ_SESSION_TYPES.p2pmsg_zlib_aesgcm:
            return handler(data, statistics, dxcall=dxcall)
        return handler(data, statistics)

    def dispatch(self, type_byte: int, data: bytearray, statistics: dict, session_id=None, dxcall=None):
        """Dispatches the handling of received ARQ data based on its type.

        This method retrieves the session type corresponding to the given type byte,
        and then invokes the appropriate handler function from the `handlers` dictionary.
        If no handler is found for the given type, it logs a warning message.

        Args:
            type_byte: The integer representing the type of ARQ data received.
            data: The raw bytes of the received ARQ data.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            The result returned by the specific handler function, or None if no handler is found.
        """
        session_type = self.get_session_type_from_value(type_byte)

        self.ctx.state_manager.setARQ(False)

        if session_type and session_type in self.handlers and "handle" in self.handlers[session_type]:
            return self.call_handler(session_type, "handle", data, statistics, session_id, dxcall)
        else:
            self.log(f"Unknown handling endpoint for type: {type_byte}", isWarning=True)

    def failed(self, type_byte: int, data: bytearray, statistics: dict, session_id=None, dxcall=None):
        """Handles the failure of an ARQ session based on the provided type byte.

        This method retrieves the session type from the given type byte and calls
        the corresponding 'failed' handler if it exists within the registered handlers.
        If no handler is found, it logs a warning message indicating an unknown endpoint.

        Args:
            type_byte: The integer representing the type of ARQ session that failed.
            data: The bytearray containing the data related to the failed session.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            The result of the 'failed' handler if found, otherwise None.
        """
        session_type = self.get_session_type_from_value(type_byte)

        self.ctx.state_manager.setARQ(False)

        if session_type in self.handlers and "failed" in self.handlers[session_type]:
            return self.call_handler(session_type, "failed", data, statistics, session_id, dxcall)
        else:
            self.log(f"Unknown handling endpoint: {session_type}", isWarning=True)

    def prepare(self, data: bytearray, session_type=ARQ_SESSION_TYPES.raw, dxcall=None):
        """Prepares data for transmission based on the specified ARQ session type.

        This method checks if a prepare handler exists for the given session type
        and invokes it if available. If no handler is found, it logs a warning message.

        Args:
            data: The bytearray of data to be prepared.
            session_type: The ARQ_SESSION_TYPES enum member representing the session type.
            dxcall: The destination callsign, needed for encrypted session types.

        Returns:
            A tuple containing the prepared data and the integer value of the session type,
            or None if no prepare handler is found for the given session type.

        Raises:
            encryption.KeyMissingError: For an encrypted type if no key is known for dxcall.
        """
        if session_type in self.handlers and "prepare" in self.handlers[session_type]:
            if session_type is ARQ_SESSION_TYPES.p2pmsg_zlib_aesgcm:
                return self.handlers[session_type]["prepare"](data, dxcall), session_type.value
            return self.handlers[session_type]["prepare"](data), session_type.value
        else:
            self.log(f"Unknown preparation endpoint: {session_type}", isWarning=True)

    def transmitted(self, type_byte: int, data: bytearray, statistics: dict, session_id=None, dxcall=None):
        """Handles the successful transmission of ARQ data based on its type.

        This method retrieves the session type from the given type byte and calls
        the corresponding 'transmitted' handler if it exists within the registered handlers.
        If no handler is found, it logs a warning message indicating an unknown endpoint.

        Args:
            type_byte: The integer representing the type of ARQ data transmitted.
            data: The bytearray containing the transmitted data.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            The result of the 'transmitted' handler if found, otherwise None.
        """
        session_type = self.get_session_type_from_value(type_byte)

        self.ctx.state_manager.setARQ(False)

        if session_type in self.handlers and "transmitted" in self.handlers[session_type]:
            return self.call_handler(session_type, "transmitted", data, statistics, session_id, dxcall)
        else:
            self.log(f"Unknown handling endpoint: {session_type}", isWarning=True)

    def log(self, message, isWarning=False):
        """Logs a message with the appropriate log level.

        This method formats the message to include the class name and then logs it
        using either the `logger.warn` method if `isWarning` is True, or the
        `logger.info` method otherwise.

        Args:
            message: The message to be logged.
            isWarning: A boolean indicating whether the message should be logged as a warning.
        """
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def prepare_raw(self, data):
        """Prepares raw data for transmission.

        This method simply logs the size of the raw data being prepared and returns it as is.
        No compression or other transformations are applied to raw data.

        Args:
            data: The bytearray containing the raw data to be prepared.

        Returns:
            The raw data as a bytearray.
        """
        self.log(f"Preparing uncompressed data: {len(data)} Bytes")
        return data

    def handle_raw(self, data, statistics):
        """Handles raw data.

        This method simply logs the size of the raw data being handled and returns it as is.
        No decompression or other transformations are applied to raw data.

        Args:
            data: The bytearray containing the raw data to be handled.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            The raw data as a bytearray.
        """
        self.log(f"Handling uncompressed data: {len(data)} Bytes")
        return data

    def failed_raw(self, data, statistics):
        """Handles the failure of raw data transmission.

        This method is a placeholder for handling failures related to raw data.
        Currently, it does nothing and returns None.

        Args:
            data: The bytearray containing the raw data.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            None
        """
        return

    def transmitted_raw(self, data, statistics):
        """Handles the successful transmission of raw data.

        This method simply returns the raw data.  No decompression or other
        transformations are applied to raw data.

        Args:
            data: The bytearray containing the raw data.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            The raw data as a bytearray.
        """
        return data

    def prepare_raw_lzma(self, data):
        """Prepares raw data for transmission using LZMA compression.

        This method compresses the given data using LZMA and logs the size of the data
        before and after compression.

        Args:
            data: The bytearray containing the raw data to be compressed.

        Returns:
            The LZMA-compressed data as a bytearray.
        """
        compressed_data = lzma.compress(data)
        self.log(f"Preparing LZMA compressed data: {len(data)} Bytes >>> {len(compressed_data)} Bytes")
        return compressed_data

    def handle_raw_lzma(self, data, statistics):
        """Handles LZMA compressed raw data.

        This method decompresses the provided LZMA data and logs the size of the data
        before and after decompression.

        Args:
            data: The bytearray containing the LZMA compressed data.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            The decompressed data as a bytearray.
        """
        decompressed_data = lzma.decompress(data)
        self.log(f"Handling LZMA compressed data: {len(decompressed_data)} Bytes from {len(data)} Bytes")
        return decompressed_data

    def failed_raw_lzma(self, data, statistics):
        """Handles the failure of LZMA compressed raw data transmission.

        This method is a placeholder for handling failures related to LZMA compressed raw data.
        Currently, it does nothing and returns None.

        Args:
            data: The bytearray containing the LZMA compressed raw data.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            None
        """
        return

    def transmitted_raw_lzma(self, data, statistics):
        """Handles the successful transmission of LZMA compressed raw data.

        This method decompresses the LZMA compressed data and returns the result.

        Args:
            data: The bytearray containing the LZMA compressed data.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            The decompressed data as a bytearray.
        """
        decompressed_data = lzma.decompress(data)
        return decompressed_data

    def prepare_raw_gzip(self, data):
        """Prepares raw data for transmission using GZIP compression.

        This method compresses the given data using GZIP and logs the size of the data
        before and after compression.

        Args:
            data: The bytearray containing the raw data to be compressed.

        Returns:
            The GZIP-compressed data as a bytearray.
        """
        compressed_data = gzip.compress(data)
        self.log(f"Preparing GZIP compressed data: {len(data)} Bytes >>> {len(compressed_data)} Bytes")
        return compressed_data

    def handle_raw_gzip(self, data, statistics):
        """Handles GZIP compressed raw data.

        This method decompresses the provided GZIP data and logs the size of the data
        before and after decompression.

        Args:
            data: The bytearray containing the GZIP compressed data.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            The decompressed data as a bytearray.
        """
        decompressed_data = gzip.decompress(data)
        self.log(f"Handling GZIP compressed data: {len(decompressed_data)} Bytes from {len(data)} Bytes")
        return decompressed_data

    def failed_raw_gzip(self, data, statistics):
        """Handles the failure of GZIP compressed raw data transmission.

        This method is a placeholder for handling failures related to GZIP compressed raw data.
        Currently, it does nothing and returns None.

        Args:
            data: The bytearray containing the GZIP compressed raw data.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            None
        """
        return

    def transmitted_raw_gzip(self, data, statistics):
        """Handles the successful transmission of GZIP compressed raw data.

        This method decompresses the GZIP compressed data and returns the result.

        Args:
            data: The bytearray containing the GZIP compressed data.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            The decompressed data as a bytearray.
        """
        decompressed_data = gzip.decompress(data)
        return decompressed_data

    def prepare_p2pmsg_zlib(self, data):
        """Prepares P2PMSG data for transmission using ZLIB compression.

        This method compresses the given data using ZLIB with a specific level, wbits, and strategy,
        and logs the size of the data before and after compression. The custom compression method ensures, we can send data without a compression header

        Args:
            data: The bytearray containing the P2PMSG data to be compressed.

        Returns:
            The ZLIB-compressed data as a bytearray.
        """

        compressor = zlib.compressobj(level=6, wbits=-zlib.MAX_WBITS, strategy=zlib.Z_FILTERED)
        compressed_data = compressor.compress(data) + compressor.flush()

        self.log(f"Preparing ZLIB compressed P2PMSG data: {len(data)} Bytes >>> {len(compressed_data)} Bytes")
        return compressed_data

    def handle_p2pmsg_zlib(self, data, statistics):
        """Handles ZLIB compressed P2PMSG data.

        This method decompresses the provided ZLIB-compressed P2PMSG data,
        logs the size before and after decompression, and then triggers the
        message_received event.

        Args:
            data: The bytearray containing the ZLIB compressed P2PMSG data.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            The decompressed data as a bytearray.
        """
        decompressor = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        decompressed_data = decompressor.decompress(data)
        decompressed_data += decompressor.flush()

        self.log(f"Handling ZLIB compressed P2PMSG data: {len(decompressed_data)} Bytes from {len(data)} Bytes")
        message_received(self.ctx, decompressed_data, statistics)
        return decompressed_data

    def failed_p2pmsg_zlib(self, data, statistics):
        """Handles failed ZLIB compressed P2PMSG data.

        This method decompresses the ZLIB compressed data, logs information about the failure,
        and triggers a message_failed event.

        Args:
            data: The bytearray containing the ZLIB compressed P2PMSG data.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            The decompressed data as a bytearray.
        """
        decompressor = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        decompressed_data = decompressor.decompress(data)
        decompressed_data += decompressor.flush()

        self.log(
            f"Handling failed ZLIB compressed P2PMSG data: {len(decompressed_data)} Bytes from {len(data)} Bytes",
            isWarning=True,
        )
        message_failed(self.ctx, decompressed_data, statistics)
        return decompressed_data

    def transmitted_p2pmsg_zlib(self, data, statistics):
        """Handles the successful transmission of ZLIB compressed P2PMSG data.

        This method decompresses the provided ZLIB compressed P2PMSG data,
        logs the size before and after decompression, and then triggers the
        message_transmitted event.

        Args:
            data: The bytearray containing the ZLIB compressed P2PMSG data.
            statistics: A dictionary containing statistics related to the ARQ session.

        Returns:
            The decompressed data as a bytearray.
        """
        # Create a decompression object with the same wbits setting used for compression
        decompressor = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        decompressed_data = decompressor.decompress(data)
        decompressed_data += decompressor.flush()

        message_transmitted(self.ctx, decompressed_data, statistics)
        return decompressed_data

    def prepare_p2pmsg_zlib_aesgcm(self, data, dxcall):
        """Compresses P2PMSG data like p2pmsg_zlib, then encrypts it with the key of dxcall.

        Raises:
            encryption.KeyMissingError: If no key has been entered for dxcall.
        """
        key = self.ctx.station_keys.get(dxcall)
        if key is None:
            raise encryption.KeyMissingError(f"No encryption key for {dxcall}")
        compressed_data = self.prepare_p2pmsg_zlib(data)
        encrypted_data = encryption.encrypt(key, compressed_data)
        self.log(f"Encrypted P2PMSG data for {dxcall}: {len(compressed_data)} Bytes >>> {len(encrypted_data)} Bytes")
        return encrypted_data

    def handle_p2pmsg_zlib_aesgcm(self, data, statistics, dxcall=None):
        """Handles an encrypted P2PMSG. If the key of dxcall is unknown or wrong, the
        message is kept encrypted until the user enters the key.

        Returns:
            The decrypted, decompressed data, or None if the message is pending.
        """
        self.log(f"Handling encrypted P2PMSG data from {dxcall}: {len(data)} Bytes")
        return encrypted_message_received(self.ctx, dxcall, data, statistics)

    def _decrypt_own_p2pmsg(self, data, dxcall):
        """Decrypts a message we sent, to update its database entry afterwards."""
        key = self.ctx.station_keys.get(dxcall)
        if key is None:
            self.log(f"Key for {dxcall} was removed, can't update the sent message", isWarning=True)
            return None
        try:
            return decompress_p2pmsg(encryption.decrypt(key, data))
        except encryption.DecryptionError:
            self.log(f"Key for {dxcall} was changed, can't update the sent message", isWarning=True)
            return None

    def failed_p2pmsg_zlib_aesgcm(self, data, statistics, dxcall=None):
        decompressed_data = self._decrypt_own_p2pmsg(data, dxcall)
        if decompressed_data is not None:
            message_failed(self.ctx, decompressed_data, statistics)
        return decompressed_data

    def transmitted_p2pmsg_zlib_aesgcm(self, data, statistics, dxcall=None):
        decompressed_data = self._decrypt_own_p2pmsg(data, dxcall)
        if decompressed_data is not None:
            message_transmitted(self.ctx, decompressed_data, statistics, encrypted=True)
        return decompressed_data

    def prepare_p2p_connection(self, data):
        """Prepares P2P connection data for transmission using ZLIB compression.

        This method compresses the provided data using ZLIB with specific settings for
        peer-to-peer connection sessions. It logs the size of the data before and after
        compression and prints the current P2P connection sessions.

        Args:
            data: The bytearray containing the P2P connection data to be compressed.

        Returns:
            The ZLIB-compressed data as a bytearray.
        """

        compressor = zlib.compressobj(level=6, wbits=-zlib.MAX_WBITS, strategy=zlib.Z_FILTERED)
        compressed_data = compressor.compress(data) + compressor.flush()

        self.log(f"Preparing zlib compressed P2P_CONNECTION data: {len(data)} Bytes >>> {len(compressed_data)} Bytes")
        print(self.ctx.state_manager.p2p_connection_sessions)
        return compressed_data

    def get_p2p_connection_sessions(self, session_id=None):
        """Returns the P2P connection session(s) a P2P_CONNECTION ARQ transfer belongs to.

        The ARQ session id equals the id of the owning P2P connection session. If the
        id is unknown, all P2P connection sessions are returned (legacy behaviour).

        Args:
            session_id: The ARQ / P2P connection session id, if known.

        Returns:
            list: The matching P2PConnection objects.
        """
        sessions = self.ctx.state_manager.p2p_connection_sessions
        if session_id is not None:
            if session_id in sessions:
                return [sessions[session_id]]
            self.log(f"No P2P connection session found for id {session_id}", isWarning=True)
            return []
        return list(sessions.values())

    def handle_p2p_connection(self, data, statistics, session_id=None):
        decompressor = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        decompressed_data = decompressor.decompress(data)
        decompressed_data += decompressor.flush()

        self.log(f"Handling gzip compressed P2P_CONNECTION data: {len(decompressed_data)} Bytes from {len(data)} Bytes")
        for session in self.get_p2p_connection_sessions(session_id):
            session.received_arq(decompressed_data)

    def failed_p2p_connection(self, data, statistics, session_id=None):
        decompressor = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        decompressed_data = decompressor.decompress(data)
        decompressed_data += decompressor.flush()
        self.log(
            f"Handling failed gzip compressed P2P_CONNECTION data: {len(decompressed_data)} Bytes from {len(data)} Bytes",
            isWarning=True,
        )
        for session in self.get_p2p_connection_sessions(session_id):
            session.failed_arq()

    def transmitted_p2p_connection(self, data, statistics, session_id=None):
        decompressor = zlib.decompressobj(wbits=-zlib.MAX_WBITS)
        decompressed_data = decompressor.decompress(data)
        decompressed_data += decompressor.flush()
        for session in self.get_p2p_connection_sessions(session_id):
            session.transmitted_arq(decompressed_data)
