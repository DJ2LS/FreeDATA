"""Unit tests for API / DB behaviour that does not need a running server:
single-message GET, broadcast DB helpers, broadcast priority coercion, the
channel_busy state field and the GUI-only config change (no modem restart)."""

import asyncio
import base64
import json
import os
import queue
import shutil
import time
import types
import unittest

from fastapi import HTTPException

import testenv  # noqa: F401  isolates config + message DB, must precede freedata_server imports
from freedata_server.context import AppContext
from freedata_server.config import CONFIG
from freedata_server.message_p2p import MessageP2P
from freedata_server.message_system_db_broadcasts import DatabaseManagerBroadcasts
from freedata_server.message_system_db_messages import DatabaseManagerMessages
from freedata_server import command_norm
from freedata_server.api.config import post_config
from freedata_server.api.freedata import get_freedata_message


class TestBroadcastDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = AppContext(testenv.config_path())
        cls.ctx.config_manager.read()
        cls.db = DatabaseManagerBroadcasts(cls.ctx)
        cls.msg_db = DatabaseManagerMessages(cls.ctx)

    @classmethod
    def tearDownClass(cls):
        cls.ctx.shutdown()

    def add_broadcast(self, msg_id, domain, priority=3):
        ok = self.db.process_broadcast_message(
            id=msg_id,
            origin="AA1AAA-0",
            timestamp=time.time(),
            burst_index=1,
            burst_data=base64.b64encode(b"hello").decode(),
            total_bursts=2,  # incomplete on purpose, no checksum needed
            checksum=None,
            domain=domain,
            msg_type="MESSAGE",
            priority=priority,
            is_read=False,
            direction="receive",
            status="received",
        )
        self.assertTrue(ok)

    def test_get_per_domain_is_read_only_and_has_priority(self):
        self.add_broadcast("bc-readonly-1", "RO1AAA-0", priority=5)

        result = self.db.get_broadcasts_per_domain_json("RO1AAA-0")
        self.assertEqual(result["RO1AAA-0"][0]["priority"], 5)
        # GET must not mark anything read
        self.assertEqual(self.db.get_broadcast_domains_json()["RO1AAA-0"]["unread_count"], 1)

        self.assertEqual(self.db.mark_domain_as_read("RO1AAA-0"), 1)
        self.assertEqual(self.db.get_broadcast_domains_json()["RO1AAA-0"]["unread_count"], 0)

    def test_delete_unknown_returns_not_found(self):
        result = self.db.delete_broadcast_message_or_domain("does-not-exist")
        self.assertEqual(result["status"], "not_found")

        self.add_broadcast("bc-delete-1", "DEL1AA-0")
        result = self.db.delete_broadcast_message_or_domain("DEL1AA-0")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["deleted"], 1)

    def test_get_message_returns_object_or_404(self):
        msg = MessageP2P.from_api_params("AA1AAA-0", {"destination": "BB1BBB-0", "body": "hi"})
        self.msg_db.add_message(MessageP2P.to_dict(msg), statistics={})

        response = asyncio.run(get_freedata_message(msg.id, self.ctx))
        self.assertEqual(response.status_code, 200)
        body = json.loads(response.body)
        self.assertIsInstance(body, dict)
        self.assertEqual(body["id"], msg.id)

        with self.assertRaises(HTTPException) as cm:
            asyncio.run(get_freedata_message("does-not-exist", self.ctx))
        self.assertEqual(cm.exception.status_code, 404)

    def test_state_event_has_channel_busy(self):
        sm = self.ctx.state_manager
        sm.set_channel_busy_condition_traffic(False)
        sm.set_channel_busy_condition_codec2(False)
        self.assertFalse(sm.get_state_event(False)["channel_busy"])
        sm.set_channel_busy_condition_traffic(True)
        self.assertTrue(sm.get_state_event(True)["channel_busy"])
        sm.set_channel_busy_condition_traffic(False)


class TestNormPriority(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = AppContext(testenv.config_path())
        cls.ctx.config_manager.read()

    @classmethod
    def tearDownClass(cls):
        cls.ctx.shutdown()

    def make(self, **extra):
        params = {
            "origin": "AA1AAA-1",
            "domain": "BB1BBB-1",
            "gridsquare": "JN48ea",
            "type": "MESSAGE",
            "data": base64.b64encode(b"hi").decode(),
        }
        params.update(extra)
        return command_norm.Norm(self.ctx, params)

    def test_priority_coerced_to_int(self):
        self.assertEqual(self.make(priority="3").priority, 3)
        self.assertEqual(self.make(priority=2).priority, 2)
        self.assertEqual(self.make().priority, 1)
        self.assertEqual(self.make(priority="high").priority, 1)
        self.assertEqual(self.make(priority=9).priority, 1)


class TestConfigRestart(unittest.TestCase):
    def setUp(self):
        path = os.path.join(os.path.dirname(testenv.config_path()), "config-restart-test.ini")
        shutil.copyfile(testenv.CONFIG_TEMPLATE, path)
        self.ctx = types.SimpleNamespace(modem_service=queue.Queue())
        self.ctx.config_manager = CONFIG(self.ctx, path)

    def post(self, changes):
        cfg = self.ctx.config_manager.read()
        cfg["STATION"]["mycall"] = "AA1AAA"
        cfg["STATION"]["mygrid"] = "JN48ea"
        for section, values in changes.items():
            cfg[section].update(values)
        return asyncio.run(post_config(cfg, self.ctx))

    def test_gui_only_change_does_not_restart(self):
        self.post({})  # normalise station values first
        while not self.ctx.modem_service.empty():
            self.ctx.modem_service.get()

        result = self.post({"GUI": {"distance_unit": "mi"}})
        self.assertEqual(result["GUI"]["distance_unit"], "mi")
        self.assertTrue(self.ctx.modem_service.empty())

    def test_modem_change_restarts(self):
        self.post({})
        while not self.ctx.modem_service.empty():
            self.ctx.modem_service.get()

        self.post({"MODEM": {"tx_delay": 123}})
        self.assertEqual(self.ctx.modem_service.get_nowait(), "restart")


if __name__ == "__main__":
    unittest.main()
