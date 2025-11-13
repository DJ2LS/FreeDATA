import sys

sys.path.append("freedata_server")

import unittest
import queue
import numpy as np
import base64

from config import CONFIG
from context import AppContext
from message_p2p import MessageP2P
from message_system_db_messages import DatabaseManagerMessages
from event_manager import EventManager


class TestMessageP2P(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = AppContext("freedata_server/config.ini.example")
        cls.ctx.config_manager.read()

        cls.event_manager = cls.ctx.event_manager
        cls.database_manager = DatabaseManagerMessages(cls.ctx)
        cls.mycall = f"{cls.ctx.config_manager.config['STATION']['mycall']}-{cls.ctx.config_manager.config['STATION']['myssid']}"

    @classmethod
    def tearDownClass(cls):
        # Wichtig: Alles herunterfahren!
        cls.ctx.shutdown()

    def test_from_api_params(self):
        api_params = {
            "destination": "DJ2LS-3",
            "body": "Hello World!",
        }
        message = MessageP2P.from_api_params(self.mycall, api_params)
        self.assertEqual(message.destination, api_params["destination"])
        self.assertEqual(message.body, api_params["body"])

    def test_to_payload_with_attachment(self):
        attachment = {
            "name": "test.gif",
            "type": "image/gif",
            "data": str(base64.b64encode(np.random.bytes(1024)), "utf-8"),
        }
        apiParams = {"destination": "DJ2LS-3", "body": "Hello World!", "attachments": [attachment]}
        message = MessageP2P.from_api_params(self.mycall, apiParams)

        payload = message.to_payload()
        received_message = MessageP2P.from_payload(payload)

        self.assertEqual(message.origin, received_message.origin)
        self.assertEqual(message.destination, received_message.destination)
        self.assertEqual(len(received_message.attachments), 1)
        self.assertEqual(received_message.attachments[0]["name"], attachment["name"])

    def test_to_payload_with_attachment_and_database(self):
        attachment = {
            "name": "test.gif",
            "type": "image/gif",
            "data": str(base64.b64encode(np.random.bytes(1024)), "utf-8"),
        }
        apiParams = {"destination": "DJ2LS-3", "body": "Hello World!", "attachments": [attachment]}
        message = MessageP2P.from_api_params(self.mycall, apiParams)

        payload = message.to_payload()
        received_message = MessageP2P.from_payload(payload)
        received_message_dict = MessageP2P.to_dict(received_message)
        self.database_manager.add_message(received_message_dict, statistics={})

        result = self.database_manager.get_message_by_id(message.id)

        self.assertEqual(message.origin, received_message.origin)
        self.assertEqual(message.destination, received_message.destination)
        self.assertEqual(result["is_read"], True)
        self.assertEqual(result["destination"], message.destination)


if __name__ == "__main__":
    unittest.main()
