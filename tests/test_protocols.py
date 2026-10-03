import queue
import time
import unittest
import testenv  # noqa: F401  isolates config + message DB, must precede freedata_server imports
from freedata_server.context import AppContext

from freedata_server.command_ping import PingCommand
from freedata_server.command_cq import CQCommand
from freedata_server import frame_handler
from freedata_server import frame_dispatcher


class TestProtocols(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a full AppContext
        cls.ctx = AppContext(testenv.config_path())
        # TESTMODE: no audio devices needed, and events are mirrored to TESTMODE_EVENTS,
        # which - unlike event_manager.queues[0] - is not drained by the websocket worker
        cls.ctx.TESTMODE = True
        cls.ctx.startup()

        frame_handler.TESTMODE = True

        cls.config = cls.ctx.config_manager.config
        cls.state_manager = cls.ctx.state_manager
        cls.event_manager = cls.ctx.event_manager
        cls.modem = cls.ctx.rf_modem  # if already started, otherwise create
        cls.frame_dispatcher = frame_dispatcher.DISPATCHER(cls.ctx)

    @classmethod
    def tearDownClass(cls):
        # Clean shutdown
        cls.ctx.shutdown()
        frame_handler.TESTMODE = False

    def shortcutTransmission(self, frame_bytes):
        """Inject a frame directly into the frame dispatcher."""
        self.frame_dispatcher.process_data(frame_bytes, None, len(frame_bytes), 0, 0, mode_name="TEST")

    def assertEventReceivedType(self, event_type, timeout=15):
        """Assert that an event with a specific type is received, skipping unrelated events."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                ev = self.ctx.TESTMODE_EVENTS.get(timeout=max(0.1, deadline - time.time()))
            except queue.Empty:
                break
            # received frames are reported as {"type": "frame-handler", "received": "<FRAME_TYPE>", ...}
            if isinstance(ev, dict) and ev.get("type") == "frame-handler" and ev.get("received") == event_type:
                return ev
        self.fail(f"no {event_type} event received within {timeout}s")

    def getTransmittedFrame(self, timeout=15):
        """Return the next frame a handler transmitted (broadcast as raw bytes in TESTMODE)."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                ev = self.ctx.TESTMODE_EVENTS.get(timeout=max(0.1, deadline - time.time()))
            except queue.Empty:
                break
            if isinstance(ev, (bytes, bytearray)):
                return ev
        self.fail(f"no transmitted frame received within {timeout}s")

    def testPingWithAck(self):
        # Prepare and transmit a PING
        api_params = {"dxcall": "AA1AAA-1"}
        ping_cmd = PingCommand(self.ctx, api_params)
        frame = ping_cmd.test(self.ctx)

        # Send frame to dispatcher
        self.shortcutTransmission(frame)
        self.assertEventReceivedType("PING")

        # Simulate receiving the ACK
        event_frame = self.getTransmittedFrame()
        self.shortcutTransmission(event_frame)
        self.assertEventReceivedType("PING_ACK")

        print("OK: PING/PING_ACK successfully verified.")

    def testCQWithQRV(self):
        self.ctx.config_manager.config["STATION"]["respond_to_cq"] = True
        self.state_manager.set_channel_busy_condition_codec2(False)

        # Prepare and transmit a CQ
        api_params = {}
        cq_cmd = CQCommand(self.ctx, api_params)
        frame = cq_cmd.test(self.ctx.TESTMODE_EVENTS)

        # Send frame to dispatcher
        self.shortcutTransmission(frame)
        self.assertEventReceivedType("CQ")

        # Simulate receiving the QRV
        event_frame = self.getTransmittedFrame()
        self.shortcutTransmission(event_frame)
        self.assertEventReceivedType("QRV")

        print("OK: CQ/QRV successfully verified.")


if __name__ == "__main__":
    unittest.main()
