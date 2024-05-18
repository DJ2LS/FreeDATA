import sys
sys.path.append('freedata_server')
import numpy as np

import unittest
from config import CONFIG
from message_p2p import MessageP2P
from message_system_db_messages import DatabaseManagerMessages
from event_manager import EventManager
import queue
import base64

class TestDataFrameFactory(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_manager = CONFIG('freedata_server/config.ini.example')
        cls.config = config_manager.read()

        cls.event_queue = queue.Queue()
        cls.event_manager = EventManager([cls.event_queue])
        cls.mycall = f"{cls.config['STATION']['mycall']}-{cls.config['STATION']['myssid']}"
        cls.database_manager = DatabaseManagerMessages(cls.event_manager)

    def testFromApiParams(self):
        api_params = {
            'destination': 'DJ2LS-3',
            'body': 'Hello World!',
        }
        message = MessageP2P.from_api_params(self.mycall, api_params)
        self.assertEqual(message.destination, api_params['destination'])
        self.assertEqual(message.body, api_params['body'])

    def testToPayloadWithAttachment(self):
        attachment = {
            'name': 'test.gif',
            'type': 'image/gif',
            'data': str(base64.b64encode(np.random.bytes(1024)), 'utf-8')
        }
        apiParams = {'destination': 'DJ2LS-3', 'body': 'Hello World!', 'attachments': [attachment]}
        message = MessageP2P.from_api_params(self.mycall, apiParams)

        payload = message.to_payload()
        received_message = MessageP2P.from_payload(payload)
        self.assertEqual(message.origin, received_message.origin)
        self.assertEqual(message.destination, received_message.destination)
        self.assertCountEqual(message.attachments, received_message.attachments)
        # FIXME...
        #self.assertEqual(attachment['data'], received_message.attachments[0]['data'])

    def testToPayloadWithAttachmentAndDatabase(self):
        attachment = {
            'name': 'test.gif',
            'type': 'image/gif',
            'data': str(base64.b64encode(np.random.bytes(1024)), 'utf-8')
        }
        apiParams = {'destination': 'DJ2LS-3', 'body': 'Hello World!', 'attachments': [attachment]}
        message = MessageP2P.from_api_params(self.mycall, apiParams)

        payload = message.to_payload()
        received_message = MessageP2P.from_payload(payload)
        received_message_dict = MessageP2P.to_dict(received_message)
        self.database_manager.add_message(received_message_dict, statistics={})

        self.assertEqual(message.origin, received_message.origin)
        self.assertEqual(message.destination, received_message.destination)
        self.assertCountEqual(message.attachments, received_message.attachments)
        result = self.database_manager.get_message_by_id(message.id)
        self.assertEqual(result["is_read"], True)
        self.assertEqual(result["destination"], message.destination)





if __name__ == '__main__':
    unittest.main()
