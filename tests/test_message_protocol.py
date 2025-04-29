import sys
import time
import unittest
import unittest.mock
import queue
import threading
import random
import structlog
import base64
import numpy as np

sys.path.append('freedata_server')

from config import CONFIG
from context import AppContext
from event_manager import EventManager
from state_manager import StateManager
from data_frame_factory import DataFrameFactory
from frame_dispatcher import DISPATCHER
import codec2
import command_message_send


class TestModem:
    def __init__(self, event_q, state_q):
        self.data_queue_received = queue.Queue()
        self.demodulator = unittest.mock.Mock()
        self.event_manager = EventManager([event_q])
        self.logger = structlog.get_logger('Modem')
        self.states = StateManager(state_q)

    def getFrameTransmissionTime(self, mode):
        samples = 0
        c2instance = codec2.open_instance(mode.value)
        samples += codec2.api.freedv_get_n_tx_preamble_modem_samples(c2instance)
        samples += codec2.api.freedv_get_n_tx_modem_samples(c2instance)
        samples += codec2.api.freedv_get_n_tx_postamble_modem_samples(c2instance)
        time = samples / 8000
        return time

    def transmit(self, mode, repeats: int, repeat_delay: int, frames: bytearray) -> bool:
        tx_time = self.getFrameTransmissionTime(mode) + 0.1
        self.logger.info(f"TX {tx_time} seconds...")
        threading.Event().wait(tx_time)

        transmission = {
            'mode': mode,
            'bytes': frames,
        }
        self.data_queue_received.put(transmission)


class TestMessageProtocol(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ctxISS = AppContext('freedata_server/config.ini.example')
        cls.ctxISS.config_manager.read()

        cls.ctxIRS = AppContext('freedata_server/config.ini.example')
        cls.ctxIRS.config_manager.read()

        cls.config = cls.ctx.config_manager.config
        cls.logger = structlog.get_logger("TESTS")
        cls.frame_factory = DataFrameFactory(cls.ctx)

        # ISS
        cls.iss_state_manager = StateManager(queue.Queue())
        cls.iss_state_manager.set_channel_busy_condition_codec2(False)
        cls.iss_event_manager = EventManager([queue.Queue()])
        cls.iss_event_queue = queue.Queue()
        cls.iss_state_queue = queue.Queue()
        cls.iss_modem = TestModem(cls.iss_event_queue, cls.iss_state_queue)
        cls.iss_frame_dispatcher = DISPATCHER(cls.ctx)

        # IRS
        cls.irs_state_manager = StateManager(queue.Queue())
        cls.irs_event_manager = EventManager([queue.Queue()])
        cls.irs_event_queue = queue.Queue()
        cls.irs_state_queue = queue.Queue()
        cls.irs_modem = TestModem(cls.irs_event_queue, cls.irs_state_queue)
        cls.irs_frame_dispatcher = DISPATCHER(cls.ctx)

        cls.loss_probability = 30
        cls.channels_running = True

    @classmethod
    def tearDownClass(cls):
        cls.ctx.shutdown()

    def channelWorker(self, modem_transmit_queue: queue.Queue, frame_dispatcher: DISPATCHER):
        while self.channels_running:
            try:
                transmission = modem_transmit_queue.get(timeout=1)
                transmission["bytes"] += bytes(2)  # simulate CRC
                if random.randint(0, 100) < self.loss_probability:
                    self.logger.info(f"[{threading.current_thread().name}] Frame lost...")
                    continue
                frame_dispatcher.process_data(transmission['bytes'], None, len(transmission['bytes']), 0, 0)
            except queue.Empty:
                continue
        self.logger.info(f"[{threading.current_thread().name}] Channel closed.")

    def waitForSession(self, event_queue, outbound=False):
        key = 'arq-transfer-outbound' if outbound else 'arq-transfer-inbound'
        while self.channels_running:
            try:
                ev = event_queue.get(timeout=2)
                if key in ev and ('success' in ev[key] or 'ABORTED' in ev[key]):
                    self.logger.info(f"[{threading.current_thread().name}] {key} session ended.")
                    break
            except queue.Empty:
                continue

    def establishChannels(self):
        self.channels_running = True
        self.iss_to_irs_channel = threading.Thread(target=self.channelWorker,
                                                   args=[self.iss_modem.data_queue_received, self.irs_frame_dispatcher],
                                                   name="ISS->IRS")
        self.irs_to_iss_channel = threading.Thread(target=self.channelWorker,
                                                   args=[self.irs_modem.data_queue_received, self.iss_frame_dispatcher],
                                                   name="IRS->ISS")
        self.iss_to_irs_channel.start()
        self.irs_to_iss_channel.start()

    def waitAndCloseChannels(self):
        self.waitForSession(self.iss_event_queue, outbound=True)
        self.channels_running = False
        self.waitForSession(self.irs_event_queue, outbound=False)
        self.iss_to_irs_channel.join()
        self.irs_to_iss_channel.join()

    def testMessageViaSession(self):
        self.loss_probability = 0  # no loss
        self.establishChannels()

        params = {
            'destination': "AA1AAA-1",
            'body': 'Hello World',
        }

        command = command_message_send.SendMessageCommand(self.ctx, params)
        command.run()

        self.waitAndCloseChannels()


if __name__ == '__main__':
    unittest.main()
