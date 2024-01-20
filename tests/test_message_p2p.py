import sys
sys.path.append('modem')
import numpy as np

import unittest
from config import CONFIG
from message_p2p import MessageP2P

class TestDataFrameFactory(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_manager = CONFIG('modem/config.ini.example')
        cls.config = config_manager.read()
        cls.mycall = f"{cls.config['STATION']['mycall']}-{cls.config['STATION']['myssid']}"


    def testFromApiParams(self):
        api_params = {
            'dxcall': 'DJ2LS-3',
            'body': 'Hello World!',
        }
        message = MessageP2P.from_api_params(self.mycall, api_params)
        self.assertEqual(message.destination, api_params['dxcall'])
        self.assertEqual(message.body, api_params['body'])

    def testToPayloadWithAttachment(self):
        attachment = {
            'name': 'test.gif',
            'type': 'image/gif',
            'data': np.random.bytes(1024)
        }
        message = MessageP2P(self.mycall, 'DJ2LS-3', 'Hello World!', [attachment])
        payload = message.to_payload()

        received_message = MessageP2P.from_payload(payload)
        self.assertEqual(message.origin, received_message.origin)
        self.assertEqual(message.destination, received_message.destination)
        self.assertCountEqual(message.attachments, received_message.attachments)
        self.assertEqual(attachment['data'], received_message.attachments[0]['data'])

if __name__ == '__main__':
    unittest.main()
