import sys
sys.path.append('modem')

import unittest
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

class TestARQSession(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_manager = CONFIG('modem/config.ini.example')
        cls.config = config_manager.read()

        cls.logger = structlog.get_logger("TESTS")

        # ISS
        cls.iss_modem_transmit_queue = queue.Queue()
        cls.iss_state_manager = StateManager(queue.Queue())
        cls.iss_event_queue = queue.Queue()
        cls.iss_frame_dispatcher = DISPATCHER(cls.config, 
                                          cls.iss_event_queue, 
                                          cls.iss_state_manager, 
                                          queue.Queue(),
                                          cls.iss_modem_transmit_queue)

        # IRS
        cls.irs_modem_transmit_queue = queue.Queue()
        cls.irs_state_manager = StateManager(queue.Queue())
        cls.irs_event_queue = queue.Queue()
        cls.irs_frame_dispatcher = DISPATCHER(cls.config, 
                                          cls.irs_event_queue, 
                                          cls.irs_state_manager, 
                                          queue.Queue(),
                                          cls.irs_modem_transmit_queue)
        
        # Frame loss probability in %
        cls.loss_probability = 50


    def channelWorker(self, modem_transmit_queue: queue, frame_dispatcher: DISPATCHER):
        while True:
            transmission_item = modem_transmit_queue.get()
            frame_bytes = bytes(transmission_item['frame'])
            if random.randint(0, 100) < self.loss_probability:
                self.logger.info(f"[{threading.current_thread().name}] Frame lost...")
                continue
            self.logger.info(f"[{threading.current_thread().name}] Redirecting frame")
            frame_dispatcher.new_process_data(frame_bytes, None, len(frame_bytes), 0, 0)

    def establishChannels(self):
        self.iss_to_irs_channel = threading.Thread(target=self.channelWorker, 
                                                    args=[self.iss_modem_transmit_queue, 
                                                    self.irs_frame_dispatcher],
                                                    name = "ISS to IRS channel")
        self.iss_to_irs_channel.start()

        self.irs_to_iss_channel = threading.Thread(target=self.channelWorker, 
                                                    args=[self.irs_modem_transmit_queue, 
                                                    self.iss_frame_dispatcher],
                                                    name = "IRS to ISS channel")
        self.irs_to_iss_channel.start()

    def testARQSession(self):

        # set Packet Error Rate (PER) / frame loss probability
        self.loss_probability = 30

        self.establishChannels()
        params = {
            'dxcall': "DJ2LS-3",
            'data': base64.b64encode(bytes("Hello world!", encoding="utf-8")),
        }
        cmd = ARQRawCommand(self.config, self.iss_state_manager, self.iss_event_queue, params)
        cmd.run(self.iss_event_queue, self.iss_modem_transmit_queue)
 
if __name__ == '__main__':
    unittest.main()
