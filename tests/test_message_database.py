import sys
sys.path.append('modem')
import numpy as np

import unittest
from config import CONFIG
from message_p2p import MessageP2P
from message_system_db_manager import DatabaseManager
from event_manager import EventManager
import queue

class TestDataFrameFactory(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_manager = CONFIG('modem/config.ini.example')
        cls.config = config_manager.read()

        cls.event_queue = queue.Queue()
        cls.event_manager = EventManager([cls.event_queue])
        cls.mycall = f"{cls.config['STATION']['mycall']}-{cls.config['STATION']['myssid']}"
        cls.database_manager = DatabaseManager(cls.event_manager, uri='sqlite:///:memory:')

    def testAddToDatabase(self):
        attachment = {
            'name': 'test.gif',
            'type': 'image/gif',
            'data': np.random.bytes(1024)
        }
        message = MessageP2P(self.mycall, 'DJ2LS-3', 'Hello World!', [attachment])
        payload = message.to_payload()
        received_message = MessageP2P.from_payload(payload)
        received_message_dict = MessageP2P.to_dict(received_message, received=True)
        self.database_manager.add_message(received_message_dict)

        result = self.database_manager.get_all_messages()
        self.assertEqual(result[0]["destination"], message.destination)

    def testDeleteFromDatabase(self):
        attachment = {
            'name': 'test.gif',
            'type': 'image/gif',
            'data': np.random.bytes(1024)
        }
        message = MessageP2P(self.mycall, 'DJ2LS-3', 'Hello World!', [attachment])
        payload = message.to_payload()
        received_message = MessageP2P.from_payload(payload)
        received_message_dict = MessageP2P.to_dict(received_message, received=True)
        self.database_manager.add_message(received_message_dict)

        result = self.database_manager.get_all_messages()
        message_id = result[0]["id"]
        self.database_manager.delete_message(message_id)

        result = self.database_manager.get_all_messages()
        self.assertNotIn(message_id, result)

    def testUpdateMessage(self):
        attachment = {
            'name': 'test.gif',
            'type': 'image/gif',
            'data': np.random.bytes(1024)
        }
        message = MessageP2P(self.mycall, 'DJ2LS-3', 'Hello World!', [attachment])
        payload = message.to_payload()
        received_message = MessageP2P.from_payload(payload)
        received_message_dict = MessageP2P.to_dict(received_message, received=True)
        message_id = self.database_manager.add_message(received_message_dict)

        self.database_manager.update_message(message_id, {'body' : 'hello123'})

        result = self.database_manager.get_message_by_id(message_id)
        self.assertIn('hello123', result['body'])

    def testGetAttachments(self):
        attachment1 = {
            'name': 'test1.gif',
            'type': 'image/gif',
            'data': np.random.bytes(1024)
        }
        attachment2 = {
            'name': 'test2.gif',
            'type': 'image/gif',
            'data': np.random.bytes(1024)
        }
        attachment3 = {
            'name': 'test3.gif',
            'type': 'image/gif',
            'data': np.random.bytes(1024)
        }
        message = MessageP2P(self.mycall, 'DJ2LS-3', 'Hello World!', [attachment1, attachment2, attachment3])
        payload = message.to_payload()
        received_message = MessageP2P.from_payload(payload)
        received_message_dict = MessageP2P.to_dict(received_message, received=True)
        message_id = self.database_manager.add_message(received_message_dict)
        result = self.database_manager.get_attachments_by_message_id(message_id)
        attachment_names = [attachment['name'] for attachment in result]
        self.assertIn('test1.gif', attachment_names)
        self.assertIn('test2.gif', attachment_names)
        self.assertIn('test3.gif', attachment_names)

if __name__ == '__main__':
    unittest.main()
