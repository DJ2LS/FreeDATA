import sys
sys.path.append('freedata_server')
import numpy as np

import unittest
from config import CONFIG
from message_p2p import MessageP2P
from message_system_db_manager import DatabaseManager
from message_system_db_messages import DatabaseManagerMessages
from message_system_db_attachments import DatabaseManagerAttachments

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
        cls.database_manager_attachments = DatabaseManagerAttachments(cls.event_manager)

    def testAddToDatabase(self):
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
        result = self.database_manager.get_message_by_id(message.id)

        self.assertEqual(result["destination"], message.destination)

    def testDeleteFromDatabase(self):
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

        result = self.database_manager.get_all_messages()
        message_id = result[0]["id"]
        self.database_manager.delete_message(message_id)

        result = self.database_manager.get_all_messages()
        self.assertNotIn(message_id, result)

    def testUpdateMessage(self):
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
        print(received_message_dict)
        message_id = self.database_manager.add_message(received_message_dict, statistics={}, direction='receive')
        print(message_id)
        self.database_manager.update_message(message_id, {'body' : 'hello123'})

        result = self.database_manager.get_message_by_id(message_id)
        self.assertIn('hello123', result['body'])

    def testGetAttachments(self):
        attachment1 = {
            'name': 'test1.gif',
            'type': 'image/gif',
            'data': str(base64.b64encode(np.random.bytes(1024)), 'utf-8')
        }
        attachment2 = {
            'name': 'test2.gif',
            'type': 'image/gif',
            'data': str(base64.b64encode(np.random.bytes(1024)), 'utf-8')
        }
        attachment3 = {
            'name': 'test3.gif',
            'type': 'image/gif',
            'data': str(base64.b64encode(np.random.bytes(1024)), 'utf-8')
        }
        apiParams = {'destination': 'DJ2LS-3', 'body': 'Hello World!', 'attachments': [attachment1, attachment2, attachment3]}
        message = MessageP2P.from_api_params(self.mycall, apiParams)
        payload = message.to_payload()
        received_message = MessageP2P.from_payload(payload)
        received_message_dict = MessageP2P.to_dict(received_message)
        message_id = self.database_manager.add_message(received_message_dict, statistics={})
        result = self.database_manager_attachments.get_attachments_by_message_id(message_id)
        attachment_names = [attachment['name'] for attachment in result]
        self.assertIn('test1.gif', attachment_names)
        self.assertIn('test2.gif', attachment_names)
        self.assertIn('test3.gif', attachment_names)

    def testIncrementAttempts(self):
        apiParams = {'destination': 'DJ2LS-3', 'body': 'Hello World!', 'attachments': []}
        message = MessageP2P.from_api_params(self.mycall, apiParams)
        payload = message.to_payload()
        received_message = MessageP2P.from_payload(payload)
        received_message_dict = MessageP2P.to_dict(received_message)
        message_id = self.database_manager.add_message(received_message_dict,statistics={},)
        self.database_manager.increment_message_attempts(message_id)
        result = self.database_manager.get_message_by_id(message_id)
        self.assertEqual(result["attempt"], 1)


if __name__ == '__main__':
    unittest.main()
