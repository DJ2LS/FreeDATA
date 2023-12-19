import sys
sys.path.append('modem')

import unittest
import unittest.mock
from config import CONFIG
import helpers
import queue
import threading
import base64
from command_arq_raw import ARQRawCommand
from state_manager import StateManager
from frame_dispatcher import DISPATCHER
import random
import structlog
import numpy as np
from event_manager import EventManager

class TestModem:
    def __init__(self):
        self.data_queue_received = queue.Queue()
        self.demodulator = unittest.mock.Mock()
        self.event_manager = EventManager([queue.Queue()])

    def transmit(self, mode, repeats: int, repeat_delay: int, frames: bytearray) -> bool:
        self.data_queue_received.put(frames)

class TestARQSession(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_manager = CONFIG('modem/config.ini.example')
        cls.config = config_manager.read()

        cls.logger = structlog.get_logger("TESTS")

        # ISS
        cls.iss_modem = TestModem()
        cls.iss_state_manager = StateManager(queue.Queue())
        cls.iss_event_queue = queue.Queue()
        cls.iss_frame_dispatcher = DISPATCHER(cls.config, 
                                          cls.iss_event_queue, 
                                          cls.iss_state_manager, 
                                          cls.iss_modem)

        # IRS
        cls.irs_modem = TestModem()
        cls.irs_state_manager = StateManager(queue.Queue())
        cls.irs_event_queue = queue.Queue()
        cls.irs_frame_dispatcher = DISPATCHER(cls.config, 
                                          cls.irs_event_queue, 
                                          cls.irs_state_manager, 
                                          cls.irs_modem)
        
        # Frame loss probability in %
        cls.loss_probability = 30



    def channelWorker(self, modem_transmit_queue: queue, frame_dispatcher: DISPATCHER):
        while True:
            frame_bytes = modem_transmit_queue.get()
            if random.randint(0, 100) < self.loss_probability:
                self.logger.info(f"[{threading.current_thread().name}] Frame lost...")
                continue
            frame_dispatcher.new_process_data(frame_bytes, None, len(frame_bytes), 0, 0)


    def establishChannels(self):
        self.iss_to_irs_channel = threading.Thread(target=self.channelWorker, 
                                                    args=[self.iss_modem.data_queue_received, 
                                                    self.irs_frame_dispatcher],
                                                    name = "ISS to IRS channel")
        self.iss_to_irs_channel.start()

        self.irs_to_iss_channel = threading.Thread(target=self.channelWorker, 
                                                    args=[self.irs_modem.data_queue_received, 
                                                    self.iss_frame_dispatcher],
                                                    name = "IRS to ISS channel")
        self.irs_to_iss_channel.start()

    def xtestARQSessionSmallPayload(self):
        # set Packet Error Rate (PER) / frame loss probability
        self.loss_probability = 30

        self.establishChannels()
        params = {
            'dxcall': "DJ2LS-3",
            'data': base64.b64encode(bytes("Hello world!", encoding="utf-8")),
        }
        cmd = ARQRawCommand(self.config, self.iss_state_manager, self.iss_event_queue, params)
        cmd.run(self.iss_event_queue, self.iss_modem)

    def testARQSessionLargePayload(self):
        # set Packet Error Rate (PER) / frame loss probability
        self.loss_probability = 50

        self.establishChannels()
        params = {
            'dxcall': "DJ2LS-3",
            'data': base64.b64encode(np.random.bytes(1000)),
        }
        cmd = ARQRawCommand(self.config, self.iss_state_manager, self.iss_event_queue, params)
        cmd.run(self.iss_event_queue, self.iss_modem)


if __name__ == '__main__':
    unittest.main()
