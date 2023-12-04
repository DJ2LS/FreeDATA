import sys
sys.path.append('modem')

import unittest
from config import CONFIG
from frame_dispatcher import DISPATCHER
import helpers
import queue
from state_manager import StateManager
from command_ping import PingCommand

class TestDataFrameFactory(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_manager = CONFIG('modem/config.ini.example')
        cls.config = config_manager.read()

        cls.state_manager_queue = queue.Queue()
        cls.state_manager = StateManager(cls.state_manager_queue)

        cls.event_queue = queue.Queue()

        cls.data_queue_received = queue.Queue()
        cls.modem_transmit_queue = queue.Queue()

        cls.frame_dispatcher = DISPATCHER(cls.config, 
                                          cls.event_queue, 
                                          cls.state_manager, 
                                          cls.data_queue_received,
                                          cls.modem_transmit_queue)

    def shortcutTransmission(self):
        transmission_item = self.modem_transmit_queue.get()
        frame_bytes = bytes(transmission_item['frame'])
        self.frame_dispatcher.new_process_data(frame_bytes, None, len(frame_bytes), 0, 0)

    def assertEventReceivedType(self, event_type):
        ev = self.event_queue.get()
        self.assertIn('freedata', ev)
        self.assertIn('received', ev)
        self.assertEqual(ev['received'], event_type)

    def testPingWithAck(self):
        # Run ping command
        api_params = { "dxcall": "XX1XXX-7" }
        ping_cmd = PingCommand(self.config, self.state_manager, self.event_queue, api_params)
        ping_cmd.run(self.event_queue, self.modem_transmit_queue)

        # Shortcut the transmit queue directly to the frame dispatcher
        self.shortcutTransmission()
        self.assertEventReceivedType('PING')

        # Check ACK
        self.shortcutTransmission()
        self.assertEventReceivedType('PING_ACK')    

if __name__ == '__main__':
    unittest.main()
