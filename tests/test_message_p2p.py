import sys
sys.path.append('modem')

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

    def testToPayload(self):
        api_params = {
            'dxcall': 'DJ2LS-3',
            'body': 'Hello World!',
        }
        message = MessageP2P.from_api_params(self.mycall, api_params)
        payload = message.to_payload()
        self.assertGreater(len(payload), 0)
        self.assertIsInstance(payload, bytes)

if __name__ == '__main__':
    unittest.main()
