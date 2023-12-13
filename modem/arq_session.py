import queue, threading
import codec2
import data_frame_factory
import structlog

class ARQSession():

    MODE_BY_SPEED = [
        codec2.FREEDV_MODE.datac4,
        codec2.FREEDV_MODE.datac3,
        codec2.FREEDV_MODE.datac1,
    ]

    def __init__(self, config: dict, tx_frame_queue: queue.Queue, dxcall: str):
        self.logger = structlog.get_logger(type(self).__name__)
        self.config = config

        self.dxcall = dxcall

        self.tx_frame_queue = tx_frame_queue
        self.speed_level = 0

        self.frame_factory = data_frame_factory.DataFrameFactory(self.config)

        self.id = None

        # 3 bytes for the BOF Beginning of File indicator in a data frame
        self.data_frame_bof = b"BOF"
        # 3 bytes for the EOF End of File indicator in a data frame
        self.data_frame_eof = b"EOF"

    def log(self, message, isWarning = False):
        msg = f"[{type(self).__name__}]: {message}"
        logger = self.logger.warn if isWarning else self.logger.info
        logger(msg)

    def get_mode_by_speed_level(self, speed_level):
        return self.MODE_BY_SPEED[speed_level]

    def transmit_frame(self, frame: bytearray):
        self.log("Transmitting frame")
        modem_queue_item = {
            'mode': self.get_mode_by_speed_level(self.speed_level),
            'repeat': 1,
            'repeat_delay': 1,
            'frame': frame,
        }
        self.tx_frame_queue.put(modem_queue_item)

    def set_state(self, state):
        self.log(f"{type(self).__name__} state change from {self.state} to {state}")
        self.state = state

    def get_payload_size(self, speed_level):
        mode = self.MODE_BY_SPEED[speed_level]
        return codec2.get_bytes_per_frame(mode.value)

    def set_details(self, snr, frequency_offset):
        self.snr = snr
        self.frequency_offset = frequency_offset
