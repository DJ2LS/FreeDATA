import sys
sys.path.append('modem')

import unittest
from config import CONFIG
from frame_dispatcher import DISPATCHER
import helpers
import queue
from state_manager import StateManager
from command_ping import PingCommand
from command_cq import CQCommand
import modem
import frame_handler


class TestProtocols(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_manager = CONFIG('modem/config.ini.example')
        cls.config = config_manager.read()

        cls.state_manager_queue = queue.Queue()
        cls.state_manager = StateManager(cls.state_manager_queue)

        cls.event_queue = queue.Queue()

        cls.modem_transmit_queue = queue.Queue()

        cls.modem = modem.RF(cls.config, cls.event_queue, queue.Queue(), queue.Queue(), cls.state_manager)
        modem.TESTMODE = True
        frame_handler.TESTMODE = True

        #cls.modem.start_modem()
        cls.frame_dispatcher = DISPATCHER(cls.config, 
                                          cls.event_queue, 
                                          cls.state_manager,
                                          cls.modem)

    def shortcutTransmission(self, frame_bytes):
        self.frame_dispatcher.new_process_data(frame_bytes, None, len(frame_bytes), 0, 0)

    def assertEventReceivedType(self, event_type):
        ev = self.event_queue.get()
        self.assertIn('freedata', ev)
        self.assertIn('received', ev)
        self.assertEqual(ev['received'], event_type)

    def testPingWithAck(self):
        # Run ping command
        api_params = { "dxcall": "XX1XXX-7"}
        ping_cmd = PingCommand(self.config, self.state_manager, self.event_queue, api_params)
        #ping_cmd.run(self.event_queue, self.modem)
        frame = ping_cmd.test(self.event_queue)
        # Shortcut the transmit queue directly to the frame dispatcher
        self.shortcutTransmission(frame)
        self.assertEventReceivedType('PING')

        event_frame = self.event_queue.get()
        # Check ACK
        self.shortcutTransmission(event_frame)
        self.assertEventReceivedType('PING_ACK')
        print("PING/PING ACK CHECK SUCCESSFULLY")

    def testCQWithQRV(self):
        self.config['MODEM']['respond_to_cq'] = True

        api_params = {}
        cmd = CQCommand(self.config, self.state_manager, self.event_queue, api_params)
        #cmd.run(self.event_queue, self.modem)
        frame = cmd.test(self.event_queue)

        self.shortcutTransmission(frame)
        self.assertEventReceivedType('CQ')

        event_frame = self.event_queue.get()
        # Check QRV
        self.shortcutTransmission(event_frame)
        self.assertEventReceivedType('QRV')
        print("CQ/QRV CHECK SUCCESSFULLY")

if __name__ == '__main__':
    unittest.main()
