# base class for norm transmission


import structlog
import time
from enum import IntEnum
import hashlib
from freedata_server.codec2 import FREEDV_MODE


class NORMMsgType(IntEnum):
    UNDEFINED = 0
    MESSAGE = 1  # Generic text/data message
    POSITION = 2  # GPS or grid locator info
    SITREP = 3  # Situation report
    METAR = 4  # METAR Message


class NORMMsgPriority(IntEnum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3
    ALERT = 4
    EMERGENCY = 5


class NormTransmission:
    def __init__(self, ctx):
        self.logger = structlog.get_logger(type(self).__name__)
        self.ctx = ctx

        if not self.ctx.config_manager.config["EXP"]["enable_groupchat"]:
            return

        self.origin = None
        self.domain = None

        self.frame_factory = freedata_server.data_frame_factory.DataFrameFactory(self.ctx)

    def log(self, message, isWarning=False):
        """Logs a message with session context.

        Logs a message, including the class name, session ID, and current state,
        using the appropriate log level (warning or info).

        Args:
            message: The message to be logged.
            isWarning: A boolean indicating whether the message should be logged as a warning.
        """
        msg = f"[{type(self).__name__}][origin={self.origin},domain={self.domain}][state={self.state.name}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def set_state(self, state):

        self.last_state_change_timestamp = time.time()
        if self.state == state:
            self.log(f"{type(self).__name__} state {self.state.name} unchanged.")
        else:
            self.log(
                f"{type(self).__name__} state change from {self.state.name} to {state.name} at {self.last_state_change_timestamp}"
            )
        self.state = state

    def on_frame_received(self, frame):
        """Handles received frames based on the current session state.

        This method processes incoming frames, triggering state transitions and
        data handling based on the frame type and current session state.
        It logs received frame types and ignores unknown state transitions.

        Args:
            frame: The received frame.
        """
        self.event_frame_received.set()
        self.log(f"Received {frame['frame_type']}")
        frame_type = frame["frame_type_int"]
        if self.state in self.STATE_TRANSITION and frame_type in self.STATE_TRANSITION[self.state]:
            action_name = self.STATE_TRANSITION[self.state][frame_type]
            received_data, type_byte = getattr(self, action_name)(frame)

            if isinstance(received_data, bytearray) and isinstance(type_byte, int):
                self.arq_data_type_handler.dispatch(
                    type_byte, received_data, self.update_histograms(len(received_data), len(received_data))
                )
            return

        self.log(f"Ignoring unknown transition from state {self.state.name} with frame {frame['frame_type']}")

    def encode_flags(self, msg_type, priority, is_last):
        """
        Encodes message type, priority and 'last burst' flag into a single byte.

        Supports msg_type as Enum or string (e.g., "MESSAGE").
        """
        # Convert msg_type
        if isinstance(msg_type, str):
            try:
                msg_type_enum = NORMMsgType[msg_type.upper()]
            except KeyError:
                raise ValueError(f"Invalid msg_type string: '{msg_type}'")
        elif isinstance(msg_type, NORMMsgType):
            msg_type_enum = msg_type
        else:
            raise TypeError("msg_type must be NORMMsgType or str")

        msg_type_int = int(msg_type_enum)

        # Convert priority
        if isinstance(priority, IntEnum):
            priority_int = int(priority)
        else:
            priority_int = int(priority)

        assert 0 <= msg_type_int <= 15, "msg_type must be 0–15"
        assert 0 <= priority_int <= 7, "priority must be 0–7"

        return ((1 if is_last else 0) << 7) | ((msg_type_int & 0x0F) << 3) | (priority_int & 0x07)

    def decode_flags(self, flags):
        """
        Decodes a flags byte into (is_last, msg_type, priority).

        Bit layout:
        Bit 7   → is_last
        Bits 6–3 → msg_type (0–15)
        Bits 2–0 → priority (0–7)

        Returns:
            is_last (bool),
            msg_type (NORMMsgType),
            priority (int)
        """
        is_last = bool((flags >> 7) & 0x01)
        msg_type_int = (flags >> 3) & 0x0F
        priority = flags & 0x07

        try:
            msg_type = NORMMsgType(msg_type_int)
        except ValueError:
            msg_type = NORMMsgType.UNDEFINED  # Fallback bei unbekanntem Typ

        return is_last, msg_type, priority

    def encode_burst_info(self, burst_number, total_bursts):
        return ((burst_number & 0x0F) << 4) | (total_bursts & 0x0F)

    def decode_burst_info(self, burst_info):
        burst_number = (burst_info >> 4) & 0x0F
        burst_total = burst_info & 0x0F
        return burst_number, burst_total

    def create_broadcast_id(self, timestamp: int, domain: str, checksum: str, length: int = 10) -> str:
        """
        Creates a deterministic broadcast ID using BLAKE2b.

        Args:
            timestamp (int): UNIX timestamp (int).
            domain (str): Domain/context string.
            checksum (str): Checksum string.
            length (int): Number of hex characters in result (max 128).

        Returns:
            str: Broadcast ID, e.g., 'bc_8d12fa3b4e'
        """
        base_str = f"{timestamp}:{domain}:{checksum}".encode("utf-8")
        digest = hashlib.blake2b(base_str, digest_size=length // 2).hexdigest()  # 1 hex char = 4 bits
        return f"{digest}"

    def create_and_transmit_nack_burst(self, origin, id, burst_numbers):
        burst = self.frame_factory.build_norm_nack(origin, id, burst_numbers)
        self.ctx.rf_modem.transmit(FREEDV_MODE.datac4, 1, 200, burst)
