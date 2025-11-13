import sys
import unittest
import queue
import base64
import numpy as np

from freedata_server.context import AppContext
from freedata_server.message_p2p import MessageP2P
from freedata_server.message_system_db_messages import DatabaseManagerMessages
from freedata_server.message_system_db_attachments import DatabaseManagerAttachments


class TestDatabaseMessageSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # echten Context bauen
        cls.ctx = AppContext("freedata_server/config.ini.example")
        cls.ctx.config_manager.read()

        # Komponenten über Context
        cls.event_manager = cls.ctx.event_manager
        cls.database_manager = DatabaseManagerMessages(cls.ctx)
        cls.database_manager_attachments = DatabaseManagerAttachments(cls.ctx)
        cls.mycall = f"{cls.ctx.config_manager.config['STATION']['mycall']}-{cls.ctx.config_manager.config['STATION']['myssid']}"

    @classmethod
    def tearDownClass(cls):
        # Clean shutdown after all tests
        cls.ctx.shutdown()

    def test_add_to_database(self):
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

        self.assertEqual(result["destination"], message.destination)

    def test_delete_from_database(self):
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

        messages = self.database_manager.get_all_messages()
        self.assertTrue(messages, "No messages found to delete!")

        message_id = messages[0]["id"]
        self.database_manager.delete_message(message_id)

        after_delete = self.database_manager.get_all_messages()
        ids_after_delete = [m["id"] for m in after_delete]
        self.assertNotIn(message_id, ids_after_delete)

    def test_update_message(self):
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

        message_id = self.database_manager.add_message(
            received_message_dict, statistics={}, direction="receive"
        )
        self.database_manager.update_message(message_id, {"body": "hello123"})

        result = self.database_manager.get_message_by_id(message_id)
        self.assertIn("hello123", result["body"])

    def test_get_attachments(self):
        attachments = []
        for i in range(3):
            attachments.append(
                {
                    "name": f"test{i}.gif",
                    "type": "image/gif",
                    "data": str(base64.b64encode(np.random.bytes(1024)), "utf-8"),
                }
            )

        apiParams = {"destination": "DJ2LS-3", "body": "Hello World!", "attachments": attachments}
        message = MessageP2P.from_api_params(self.mycall, apiParams)
        payload = message.to_payload()
        received_message = MessageP2P.from_payload(payload)
        received_message_dict = MessageP2P.to_dict(received_message)

        message_id = self.database_manager.add_message(received_message_dict, statistics={})
        result = self.database_manager_attachments.get_attachments_by_message_id(message_id)
        attachment_names = [attachment["name"] for attachment in result]

        for i in range(3):
            self.assertIn(f"test{i}.gif", attachment_names)

    def test_increment_attempts(self):
        apiParams = {"destination": "DJ2LS-3", "body": "Hello World!", "attachments": []}
        message = MessageP2P.from_api_params(self.mycall, apiParams)
        payload = message.to_payload()
        received_message = MessageP2P.from_payload(payload)
        received_message_dict = MessageP2P.to_dict(received_message)

        message_id = self.database_manager.add_message(received_message_dict, statistics={})
        self.database_manager.increment_message_attempts(message_id)

        result = self.database_manager.get_message_by_id(message_id)
        self.assertEqual(result["attempt"], 1)


if __name__ == "__main__":
    unittest.main()
