import sys
sys.path.append('freedata_server')

import unittest
import queue

from config import CONFIG
from frame_dispatcher import DISPATCHER
from state_manager import StateManager
from event_manager import EventManager
from command_ping import PingCommand
from command_cq import CQCommand
import modem
import frame_handler
from radio_manager import RadioManager


class TestProtocols(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_manager = CONFIG('freedata_server/config.ini.example')
        cls.config = config_manager.read()

        cls.state_manager_queue = queue.Queue()
        cls.state_manager = StateManager(cls.state_manager_queue)

        cls.event_queue = queue.Queue()
        cls.event_manager = EventManager([cls.event_queue])

        cls.radio_manager = RadioManager(cls.config, cls.state_manager, cls.event_manager, None)
        cls.modem_transmit_queue = queue.Queue()

        cls.modem = modem.RF(cls.config, cls.event_queue, queue.Queue(), queue.Queue(), cls.state_manager, cls.radio_manager)
        modem.TESTMODE = True
        frame_handler.TESTMODE = True

        cls.frame_dispatcher = DISPATCHER(
            cls.config,
            cls.event_manager,
            cls.state_manager,
            cls.modem,
            None
        )

    def shortcutTransmission(self, frame_bytes):
        """Inject a frame directly into the frame dispatcher."""
        self.frame_dispatcher.process_data(frame_bytes, None, len(frame_bytes), 0, 0, mode_name="TEST")

    def assertEventReceivedType(self, event_type):
        """Assert that an event with a specific type was received."""
        ev = self.event_queue.get(timeout=5)
        self.assertIn('type', ev)
        self.assertEqual(ev['type'], event_type)

    def testPingWithAck(self):
        # Prepare and transmit a PING
        api_params = {"dxcall": "AA1AAA-1"}
        ping_cmd = PingCommand(self.config, self.state_manager, self.event_manager, api_params)
        frame = ping_cmd.test(self.event_queue)

        # Send frame to dispatcher
        self.shortcutTransmission(frame)
        self.assertEventReceivedType('PING')

        # Simulate receiving the ACK
        event_frame = self.event_queue.get(timeout=5)
        self.shortcutTransmission(event_frame)
        self.assertEventReceivedType('PING_ACK')

        print("✅ PING/PING_ACK successfully verified.")

    def testCQWithQRV(self):
        self.config['STATION']['respond_to_cq'] = True
        self.state_manager.set_channel_busy_condition_codec2(False)

        # Prepare and transmit a CQ
        api_params = {}
        cq_cmd = CQCommand(self.config, self.state_manager, self.event_manager, api_params)
        frame = cq_cmd.test(self.event_queue)

        # Send frame to dispatcher
        self.shortcutTransmission(frame)
        self.assertEventReceivedType('CQ')

        # Simulate receiving the QRV
        event_frame = self.event_queue.get(timeout=5)
        self.shortcutTransmission(event_frame)
        self.assertEventReceivedType('QRV')

        print("✅ CQ/QRV successfully verified.")


if __name__ == '__main__':
    unittest.main()
