import sys
import time

import unittest
import unittest.mock
from freedata_server import config
from freedata_server.context import AppContext

from freedata_server import helpers
import queue
import threading
import base64
from freedata_server.command_arq_raw import ARQRawCommand
from freedata_server.state_manager import StateManager
from freedata_server.frame_dispatcher import DISPATCHER
import random
import structlog
import numpy as np
from freedata_server.event_manager import EventManager
from freedata_server.state_manager import StateManager
from freedata_server.data_frame_factory import DataFrameFactory
from freedata_server import codec2
from freedata_server import arq_session_irs
import os


class DummyCtx:
    def __init__(self):
        pass


class TestARQSession(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logger = structlog.get_logger("TESTS")

        # ISS

        cls.ctx_ISS = AppContext("freedata_server/config.ini.example")
        cls.ctx_ISS.TESTMODE = True
        cls.ctx_ISS.startup()

        # IRS
        cls.ctx_IRS = AppContext("freedata_server/config.ini.example")
        cls.ctx_IRS.TESTMODE = True
        cls.ctx_IRS.startup()

        # simulate a busy condition
        cls.ctx_IRS.state_manager.channel_busy_slot = [True, False, False, False, False]
        # Frame loss probability in %
        cls.loss_probability = 0

        cls.channels_running = False

    @classmethod
    def tearDownClass(cls):
        # Clean shutdown after all tests
        cls.ctx_IRS.shutdown()
        cls.ctx_ISS.shutdown()

    def channelWorker(self, ctx_a, ctx_b):
        while self.channels_running:
            try:
                # Station A gets the data from its transmit queue
                transmission = ctx_a.TESTMODE_TRANSMIT_QUEUE.get(timeout=1)
                print(
                    f"Station A sending: {transmission[1]}", len(transmission[1]), transmission[0]
                )

                transmission[1] += bytes(2)  # 2bytes crc simulation

                if random.randint(0, 100) < self.loss_probability:
                    self.logger.info(f"[{threading.current_thread().name}] Frame lost...")
                    continue

                # Forward data from Station A to Station B's receive queue
                if ctx_b:
                    ctx_b.TESTMODE_RECEIVE_QUEUE.put(transmission)
                    self.logger.info(f"Data forwarded to Station B")

                frame_bytes = transmission[1]
                if len(frame_bytes) == 5:
                    mode_name = "SIGNALLING_ACK"
                else:
                    mode_name = transmission[0]

                snr = 15
                ctx_b.service_manager.frame_dispatcher.process_data(
                    frame_bytes, None, len(frame_bytes), snr, 0, mode_name=mode_name
                )

            except queue.Empty:
                continue

        self.logger.info(f"[{threading.current_thread().name}] Channel closed.")

    def waitForSession(self, q, outbound=False):
        key = "arq-transfer-outbound" if outbound else "arq-transfer-inbound"
        while True and self.channels_running:
            ev = q.get()
            if key in ev and ("success" in ev[key] or "ABORTED" in ev[key]):
                self.logger.info(f"[{threading.current_thread().name}] {key} session ended.")
                break

    def establishChannels(self):
        self.channels_running = True
        self.channelA = threading.Thread(
            target=self.channelWorker, args=[self.ctx_ISS, self.ctx_IRS], name="channelA"
        )
        self.channelA.start()

        self.channelB = threading.Thread(
            target=self.channelWorker, args=[self.ctx_IRS, self.ctx_ISS], name="channelB"
        )
        self.channelB.start()

    def waitAndCloseChannels(self):
        self.waitForSession(self.ctx_ISS.TESTMODE_EVENTS, True)
        self.channels_running = False
        self.waitForSession(self.ctx_IRS.TESTMODE_EVENTS, False)
        self.channels_running = False

    def DisabledtestARQSessionSmallPayload(self):
        # set Packet Error Rate (PER) / frame loss probability
        self.loss_probability = 30

        self.establishChannels()
        params = {
            "dxcall": "AA1AAA-1",
            "data": base64.b64encode(bytes("Hello world!", encoding="utf-8")),
            "type": "raw_lzma",
        }
        cmd = ARQRawCommand(self.ctx_ISS, params)
        cmd.run()
        self.waitAndCloseChannels()
        print(self.ctx_ISS.TESTMODE_EVENTS.empty())

        while not self.ctx_ISS.TESTMODE_EVENTS.empty():
            event = self.ctx_ISS.TESTMODE_EVENTS.get()
            success = event.get("arq-transfer-outbound", {}).get("success", None)
            if success is not None:
                self.assertTrue(success, f"Test failed because of wrong success: {success}")

        # self.ctx_IRS.shutdown()
        # self.ctx_ISS.shutdown()

    def testARQSessionLargePayload(self):
        # set Packet Error Rate (PER) / frame loss probability
        self.loss_probability = 0

        self.establishChannels()
        params = {
            "dxcall": "AA1AAA-1",
            "data": base64.b64encode(np.random.bytes(1000)),
            "type": "raw_lzma",
        }
        cmd = ARQRawCommand(self.ctx_ISS, params)
        cmd.run()

        self.waitAndCloseChannels()
        # del cmd
        print(self.ctx_ISS.TESTMODE_EVENTS.empty())

        while not self.ctx_ISS.TESTMODE_EVENTS.empty():
            event = self.ctx_ISS.TESTMODE_EVENTS.get()
            success = event.get("arq-transfer-outbound", {}).get("success", None)
            if success is not None:
                self.assertTrue(success, f"Test failed because of wrong success: {success}")

        # self.ctx_IRS.shutdown()
        # self.ctx_ISS.shutdown()

    def DisabledtestARQSessionAbortTransmissionISS(self):
        # set Packet Error Rate (PER) / frame loss probability
        self.loss_probability = 0

        self.establishChannels()
        params = {
            "dxcall": "AA1AAA-1",
            "data": base64.b64encode(np.random.bytes(100)),
        }
        cmd = ARQRawCommand(self.ctx_ISS, params)
        cmd.run()

        threading.Event().wait(np.random.randint(10, 10))
        for id in self.ctx_ISS.state_manager.arq_iss_sessions:
            self.ctx_ISS.state_manager.arq_iss_sessions[id].abort_transmission()

        self.waitAndCloseChannels()

        del cmd

    def DisabledtestARQSessionAbortTransmissionIRS(self):
        # set Packet Error Rate (PER) / frame loss probability
        self.loss_probability = 0

        self.establishChannels()
        params = {
            "dxcall": "AA1AAA-1",
            "data": base64.b64encode(np.random.bytes(100)),
        }
        cmd = ARQRawCommand(self.ctx_ISS, params)
        cmd.run()

        threading.Event().wait(np.random.randint(1, 10))
        for id in self.ctx_IRS.state_manager.arq_irs_sessions:
            self.ctx_IRS.state_manager.arq_irs_sessions[id].abort_transmission()

        self.waitAndCloseChannels()
        del cmd

    def DisabledtestSessionCleanupISS(self):
        params = {
            "dxcall": "AA1AAA-1",
            "data": base64.b64encode(np.random.bytes(100)),
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
        session = arq_session_irs.ARQSessionIRS(
            self.config, self.irs_modem, "AA1AAA-1", random.randint(0, 255), self.irs_state_manager
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


if __name__ == "__main__":
    unittest.main()
