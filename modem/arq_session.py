import queue, threading
import codec2
import data_frame_factory
import structlog

class ARQSession():

    MODE_BY_SPEED = [
        codec2.FREEDV_MODE.datac4.value,
        codec2.FREEDV_MODE.datac3.value,
        codec2.FREEDV_MODE.datac1.value,
    ]

    def __init__(self, config: dict, tx_frame_queue: queue.Queue, dxcall: str):
        self.logger = structlog.get_logger(type(self).__name__)
        self.config = config

        self.dxcall = dxcall

        self.tx_frame_queue = tx_frame_queue
        self.speed_level = 0

        self.frame_factory = data_frame_factory.DataFrameFactory(self.config)

        self.id = None

    def get_mode_by_speed_level(self, speed_level):
        return self.MODE_BY_SPEED[speed_level]

    def transmit_frame(self, frame: bytearray):
        self.logger.info("Transmitting frame")
        modem_queue_item = {
            'mode': self.get_mode_by_speed_level(self.speed_level),
            'repeat': 1,
            'repeat_delay': 1,
            'frame': frame,
        }
        self.tx_frame_queue.put(modem_queue_item)

    def setState(self, state):
        self.state = state
        self.logger.info(f"state changed to {state}")

    def get_payload_size(self, speed_level):
        mode = self.MODE_BY_SPEED[speed_level]
        return codec2.get_bytes_per_frame(mode)
