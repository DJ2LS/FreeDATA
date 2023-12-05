import queue, threading
from codec2 import FREEDV_MODE
import data_frame_factory

class ARQSession():

    MODE_BY_SPEED = [
        FREEDV_MODE.datac4.value,
        FREEDV_MODE.datac3.value,
        FREEDV_MODE.datac1.value,
    ]

    def __init__(self, config: dict, tx_frame_queue: queue.Queue, dxcall: str):
        self.config = config

        self.dxcall = dxcall

        self.tx_frame_queue = tx_frame_queue
        self.speed_level = 0

        self.frame_factory = data_frame_factory.DataFrameFactory(self.config)

        self.id = None

    def get_mode_by_speed_level(self, speed_level):
        return self.MODE_BY_SPEED[speed_level]

    def transmit_frame(self, frame: bytearray):
        modem_queue_item = {
            'mode': self.get_mode_by_speed_level(self.speed_level),
            'repeat': 1,
            'repeat_delay': 1,
            'frame': frame,
        }
        self.tx_frame_queue.put(modem_queue_item)

