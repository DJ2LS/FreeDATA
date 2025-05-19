import sys
import time
sys.path.append('freedata_server')

import unittest
import unittest.mock
import config
from context import AppContext

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
from state_manager import StateManager
from data_frame_factory import DataFrameFactory
import codec2
import arq_session_irs
import os

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
        #print(mode)
        #if mode == codec2.FREEDV_MODE.signalling:
        #    time = 0.69
        #print(time)
        return time

    def transmit(self, mode, repeats: int, repeat_delay: int, frames: bytearray) -> bool:

        # Simulate transmission time
        tx_time = self.getFrameTransmissionTime(mode) + 0.1 # PTT
        self.logger.info(f"TX {tx_time} seconds...")
        threading.Event().wait(tx_time)

        transmission = {
            'mode': mode,
            'bytes': frames,
        }
        self.data_queue_received.put(transmission)

class DummyCtx:
    def __init__(self):
        pass



class TestARQSession(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # TODO:
        # ESTABLISH MODEM CHANNELS CORRECTLY SO WE ARE GETTING THE CORRESPINDING BURSTS

        cls.logger = structlog.get_logger("TESTS")

        # ISS

        cls.ctx_ISS = AppContext('freedata_server/config.ini.example')
        cls.ctx_ISS.TESTMODE = True
        cls.ctx_ISS.startup()


        # IRS
        cls.ctx_IRS = AppContext('freedata_server/config.ini.example')
        cls.ctx_IRS.TESTMODE = True
        cls.ctx_IRS.startup()

        # simulate a busy condition
        cls.ctx_IRS.state_manager.channel_busy_slot = [True, False, False, False, False]
        # Frame loss probability in %
        cls.loss_probability = 0




        cls.channels_running = False



    def channelWorker(self, modem_transmit_queue: queue.Queue, frame_dispatcher: DISPATCHER):
        while self.channels_running:
            # Transfer data between both parties
            try:
                transmission = modem_transmit_queue.get(timeout=1)
                transmission["bytes"] += bytes(2) # simulate 2 bytes crc checksum
                if random.randint(0, 100) < self.loss_probability:
                    self.logger.info(f"[{threading.current_thread().name}] Frame lost...")
                    continue

                frame_bytes = transmission['bytes']

                if len(frame_bytes) == 5:
                    mode_name = "SIGNALLING_ACK"
                else:
                    mode_name = None
                frame_dispatcher.process_data(frame_bytes, None, len(frame_bytes), 15, 0, mode_name=mode_name)
            except queue.Empty:
                continue
        self.logger.info(f"[{threading.current_thread().name}] Channel closed.")

    def waitForSession(self, q, outbound = False):
            key = 'arq-transfer-outbound' if outbound else 'arq-transfer-inbound'
            while True and self.channels_running:
                ev = q.get()
                if key in ev and ('success' in ev[key] or 'ABORTED' in ev[key]):
                    self.logger.info(f"[{threading.current_thread().name}] {key} session ended.")
                    break

    def establishChannels(self):
        self.iss_to_irs_channel = threading.Thread(target=self.channelWorker,
                                                    args=[self.ctx_ISS.rf_modem.data_queue_received,
                                                    self.ctx_IRS.service_manager.frame_dispatcher],
                                                    name = "ISS to IRS channel")
        self.iss_to_irs_channel.start()

        self.irs_to_iss_channel = threading.Thread(target=self.channelWorker, 
                                                    args=[self.ctx_IRS.rf_modem.data_queue_received,
                                                    self.ctx_ISS.service_manager.frame_dispatcher],
                                                    name = "IRS to ISS channel")
        self.irs_to_iss_channel.start()
        self.channels_running = True
    def waitAndCloseChannels(self):
        self.waitForSession(self.ctx_ISS.modem_events, True)
        self.channels_running = False
        self.waitForSession(self.ctx_IRS.modem_events, False)
        self.channels_running = False

    def DisabledtestARQSessionSmallPayload(self):
        # set Packet Error Rate (PER) / frame loss probability
        self.loss_probability = 30

        self.establishChannels()
        params = {
            'dxcall': "AA1AAA-1",
            'data': base64.b64encode(bytes("Hello world!", encoding="utf-8")),
            'type': "raw_lzma"
        }
        cmd = ARQRawCommand(self.ctx_ISS, params)
        cmd.run()
        self.waitAndCloseChannels()
        del cmd

    def testARQSessionLargePayload(self):
        # set Packet Error Rate (PER) / frame loss probability
        self.loss_probability = 0

        self.establishChannels()
        params = {
            'dxcall': "AA1AAA-1",
            'data': base64.b64encode(np.random.bytes(1000)),
            'type': "raw_lzma"
        }
        cmd = ARQRawCommand(self.ctx_ISS, params)
        cmd.run()

        self.waitAndCloseChannels()
        del cmd

    def DisabledtestARQSessionAbortTransmissionISS(self):
        # set Packet Error Rate (PER) / frame loss probability
        self.loss_probability = 0

        self.establishChannels()
        params = {
            'dxcall': "AA1AAA-1",
            'data': base64.b64encode(np.random.bytes(100)),
        }
        cmd = ARQRawCommand(self.ctx_ISS, params)
        cmd.run()

        threading.Event().wait(np.random.randint(10,10))
        for id in self.ctx_ISS.state_manager.arq_iss_sessions:
            self.ctx_ISS.state_manager.arq_iss_sessions[id].abort_transmission()

        self.waitAndCloseChannels()
        del cmd

    def DisabledtestARQSessionAbortTransmissionIRS(self):
        # set Packet Error Rate (PER) / frame loss probability
        self.loss_probability = 0

        self.establishChannels()
        params = {
            'dxcall': "AA1AAA-1",
            'data': base64.b64encode(np.random.bytes(100)),
        }
        cmd = ARQRawCommand(self.ctx_ISS, params)
        cmd.run()

        threading.Event().wait(np.random.randint(1,10))
        for id in self.ctx_IRS.state_manager.arq_irs_sessions:
            self.ctx_IRS.state_manager.arq_irs_sessions[id].abort_transmission()

        self.waitAndCloseChannels()
        del cmd

    def DisabledtestSessionCleanupISS(self):

        params = {
            'dxcall': "AA1AAA-1",
            'data': base64.b64encode(np.random.bytes(100)),
        }
        cmd = ARQRawCommand(self.config, self.iss_state_manager, self.iss_event_queue, params)
        cmd.run(self.iss_event_queue, self.iss_modem)
        for session_id in self.iss_state_manager.arq_iss_sessions:
            session = self.iss_state_manager.arq_iss_sessions[session_id]
            ISS_States = session.state_enum
            session.state = ISS_States.FAILED
            session.session_ended = time.time() - 1000
            if session.is_session_outdated():
                self.logger.info(f"session [{session_id}] outdated - deleting it")
                self.iss_state_manager.remove_arq_iss_session(session_id)
                break
        del cmd

    def DisabledtestSessionCleanupIRS(self):
        session = arq_session_irs.ARQSessionIRS(self.config,
                            self.irs_modem,
                            'AA1AAA-1',
                            random.randint(0, 255),
                            self.irs_state_manager
                                                )
        self.irs_state_manager.register_arq_irs_session(session)
        for session_id in self.irs_state_manager.arq_irs_sessions:
            session = self.irs_state_manager.arq_irs_sessions[session_id]
            irs_States = session.state_enum
            session.state = irs_States.FAILED
            session.session_ended = time.time() - 1000
            if session.is_session_outdated():
                self.logger.info(f"session [{session_id}] outdated - deleting it")
                self.irs_state_manager.remove_arq_irs_session(session_id)
                break

if __name__ == '__main__':
    unittest.main()
