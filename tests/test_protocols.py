import sys

sys.path.append("freedata_server")

import unittest
from context import AppContext
import queue

from command_ping import PingCommand
from command_cq import CQCommand
import frame_handler
import frame_dispatcher


class TestProtocols(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a full AppContext
        cls.ctx = AppContext("freedata_server/config.ini.example")
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

    def shortcutTransmission(self, frame_bytes):
        """Inject a frame directly into the frame dispatcher."""
        self.frame_dispatcher.process_data(
            frame_bytes, None, len(frame_bytes), 0, 0, mode_name="TEST"
        )

    def assertEventReceivedType(self, event_type):
        """Assert that an event with a specific type was received."""
        ev = self.ctx.event_manager.queues[0].get(timeout=5)
        self.assertIn("type", ev)
        self.assertEqual(ev["type"], event_type)

    def testPingWithAck(self):
        # Prepare and transmit a PING
        api_params = {"dxcall": "AA1AAA-1"}
        ping_cmd = PingCommand(self.ctx, api_params)
        frame = ping_cmd.test(self.ctx)

        # Send frame to dispatcher
        self.shortcutTransmission(frame)
        self.assertEventReceivedType("PING")

        # Simulate receiving the ACK
        event_frame = self.event_manager.queues[0].get(timeout=5)
        self.shortcutTransmission(event_frame)
        self.assertEventReceivedType("PING_ACK")

        print("✅ PING/PING_ACK successfully verified.")

    def testCQWithQRV(self):
        self.ctx.config_manager.config["STATION"]["respond_to_cq"] = True
        self.state_manager.set_channel_busy_condition_codec2(False)

        # Prepare and transmit a CQ
        api_params = {}
        cq_cmd = CQCommand(self.ctx, api_params)
        frame = cq_cmd.test(self.event_manager.queues[0])

        # Send frame to dispatcher
        self.shortcutTransmission(frame)
        self.assertEventReceivedType("CQ")

        # Simulate receiving the QRV
        event_frame = self.event_manager.queues[0].get(timeout=5)
        self.shortcutTransmission(event_frame)
        self.assertEventReceivedType("QRV")

        print("✅ CQ/QRV successfully verified.")


if __name__ == "__main__":
    unittest.main()
