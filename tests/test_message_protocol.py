import unittest
import unittest.mock
import queue
import threading
import random
import time
import structlog

import testenv  # noqa: F401  isolates config + message DB, must precede freedata_server imports
from freedata_server.context import AppContext
from freedata_server.event_manager import EventManager
from freedata_server.state_manager import StateManager
from freedata_server import codec2
from freedata_server import command_message_send


class TestModem:
    def __init__(self, event_q, state_q):
        self.data_queue_received = queue.Queue()
        self.demodulator = unittest.mock.Mock()
        self.event_manager = EventManager([event_q])
        self.logger = structlog.get_logger("Modem")
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
            "mode": mode,
            "bytes": frames,
        }
        self.data_queue_received.put(transmission)


class TestMessageProtocol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logger = structlog.get_logger("TESTS")

        # ISS

        cls.ctx_ISS = AppContext(testenv.config_path())
        cls.ctx_ISS.TESTMODE = True
        cls.ctx_ISS.startup()

        # IRS
        cls.ctx_IRS = AppContext(testenv.config_path())
        cls.ctx_IRS.TESTMODE = True
        cls.ctx_IRS.startup()

        # simulate a busy condition
        cls.ctx_IRS.state_manager.channel_busy_slot = [True, False, False, False, False]
        # Frame loss probability in %
        cls.loss_probability = 0

        cls.channels_running = False

    @classmethod
    def tearDownClass(cls):
        cls.ctx_IRS.shutdown()
        cls.ctx_ISS.shutdown()

    def channelWorker(self, ctx_a, ctx_b):
        while self.channels_running:
            try:
                # Station A gets the data from its transmit queue
                transmission = ctx_a.TESTMODE_TRANSMIT_QUEUE.get(timeout=1)
                print(f"Station A sending: {transmission[1]}", len(transmission[1]), transmission[0])

                transmission[1] += bytes(2)  # 2bytes crc simulation

                if random.randint(0, 100) < self.loss_probability:
                    self.logger.info(f"[{threading.current_thread().name}] Frame lost...")
                    continue

                # Forward data from Station A to Station B's receive queue
                if ctx_b:
                    ctx_b.TESTMODE_RECEIVE_QUEUE.put(transmission)
                    self.logger.info("Data forwarded to Station B")

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

    def waitForSession(self, event_queue, outbound=False, timeout=120):
        """Wait for the session-ending event and return it (None on timeout)."""
        key = "arq-transfer-outbound" if outbound else "arq-transfer-inbound"
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                ev = event_queue.get(timeout=2)
                if isinstance(ev, dict) and key in ev and ("success" in ev[key] or "ABORTED" in ev[key]):
                    self.logger.info(f"[{threading.current_thread().name}] {key} session ended.")
                    return ev
            except queue.Empty:
                continue
        return None

    def establishChannels(self):
        self.channels_running = True
        self.channelA = threading.Thread(target=self.channelWorker, args=[self.ctx_ISS, self.ctx_IRS], name="channelA")
        self.channelA.start()

        self.channelB = threading.Thread(target=self.channelWorker, args=[self.ctx_IRS, self.ctx_ISS], name="channelB")
        self.channelB.start()

    def waitAndCloseChannels(self):
        # TESTMODE_EVENTS mirrors all events and, unlike modem_events, is not drained by the websocket worker
        iss_event = self.waitForSession(self.ctx_ISS.TESTMODE_EVENTS, True)
        irs_event = self.waitForSession(self.ctx_IRS.TESTMODE_EVENTS, False)
        self.channels_running = False
        self.channelA.join()
        self.channelB.join()
        return iss_event, irs_event

    def testMessageViaSession(self):
        self.loss_probability = 0  # no loss
        self.establishChannels()

        params = {
            "destination": "AA1AAA-1",
            "body": "Hello World",
        }

        command = command_message_send.SendMessageCommand(self.ctx_ISS, params)
        command.run()

        iss_event, irs_event = self.waitAndCloseChannels()
        self.assertIsNotNone(iss_event, "no outbound session end event received")
        self.assertTrue(iss_event["arq-transfer-outbound"].get("success"), f"outbound transfer failed: {iss_event}")
        self.assertIsNotNone(irs_event, "no inbound session end event received")
        self.assertTrue(irs_event["arq-transfer-inbound"].get("success"), f"inbound transfer failed: {irs_event}")


if __name__ == "__main__":
    unittest.main()
