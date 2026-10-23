"""Tests for per-station message encryption: the AES-GCM helpers, the
encrypted ARQ data type, holding messages until a key is entered and the
station encryption API."""

import asyncio
import json
import os
import queue
import unittest

from fastapi import HTTPException

import testenv  # noqa: F401  isolates config + message DB, must precede freedata_server imports
from freedata_server import encryption
from freedata_server.context import AppContext
from freedata_server.arq_data_type_handler import ARQDataTypeHandler, ARQ_SESSION_TYPES
from freedata_server.message_p2p import MessageP2P
from freedata_server.message_system_db_encryption import DatabaseManagerEncryption
from freedata_server.message_system_db_messages import DatabaseManagerMessages
from freedata_server.message_system_db_station import DatabaseManagerStations
from freedata_server import command_message_send
from freedata_server.api.freedata import (
    get_station_encryption,
    patch_station_encryption,
    put_station_encryption_key,
    delete_station_encryption_key,
)

HEX_KEY = "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"
OTHER_HEX_KEY = "ff" * 32


def message_payload(msg_id, origin, destination, body="secret hello"):
    message = MessageP2P(msg_id, origin, destination, body, [])
    return bytearray(message.to_payload().encode("utf-8"))


class TestEncryptionPrimitives(unittest.TestCase):
    def test_round_trip(self):
        key = encryption.parse_key(HEX_KEY)
        payload = encryption.encrypt(key, b"hello")
        self.assertEqual(len(payload), len(b"hello") + encryption.OVERHEAD_BYTES)
        self.assertNotIn(b"hello", payload)
        self.assertEqual(encryption.decrypt(key, payload), b"hello")

    def test_random_nonce(self):
        key = encryption.parse_key(HEX_KEY)
        self.assertNotEqual(encryption.encrypt(key, b"hello"), encryption.encrypt(key, b"hello"))

    def test_wrong_key_and_tampering_fail(self):
        key = encryption.parse_key(HEX_KEY)
        payload = encryption.encrypt(key, b"hello")
        with self.assertRaises(encryption.DecryptionError):
            encryption.decrypt(encryption.parse_key(OTHER_HEX_KEY), payload)
        tampered = bytearray(payload)
        tampered[-1] ^= 0x01
        with self.assertRaises(encryption.DecryptionError):
            encryption.decrypt(key, tampered)
        with self.assertRaises(encryption.DecryptionError):
            encryption.decrypt(key, bytes([99]) + payload[1:])  # unknown format version
        with self.assertRaises(encryption.DecryptionError):
            encryption.decrypt(key, payload[:10])

    def test_parse_key(self):
        self.assertEqual(encryption.parse_key(HEX_KEY.upper()), bytes.fromhex(HEX_KEY))
        derived = encryption.parse_key("correct horse battery staple")
        self.assertEqual(len(derived), encryption.KEY_BYTES)
        # both stations have to derive the same key from the same passphrase
        self.assertEqual(derived, encryption.parse_key("  correct horse battery staple "))
        for bad in ["short", "", None, 123]:
            with self.assertRaises(ValueError):
                encryption.parse_key(bad)

    def test_fingerprint(self):
        key = encryption.parse_key(HEX_KEY)
        self.assertEqual(encryption.key_fingerprint(key), encryption.key_fingerprint(bytes(key)))
        self.assertNotEqual(encryption.key_fingerprint(key), encryption.key_fingerprint(bytes(32)))
        self.assertRegex(encryption.key_fingerprint(key), r"^[0-9A-F]{4}( [0-9A-F]{4}){3}$")

    def test_key_store(self):
        store = encryption.StationKeyStore()
        self.assertFalse(store.has("AA1AAA-0"))
        store.set("AA1AAA-0", bytes(32))
        self.assertTrue(store.has("AA1AAA-0"))
        self.assertIsNotNone(store.fingerprint("AA1AAA-0"))
        self.assertTrue(store.remove("AA1AAA-0"))
        self.assertFalse(store.remove("AA1AAA-0"))
        with self.assertRaises(ValueError):
            store.set("AA1AAA-0", b"short")


class TestEncryptedMessages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = AppContext(testenv.config_path())
        cls.ctx.config_manager.read()
        cls.ctx.TESTMODE = True
        cls.ctx.message_system_db_manager.initialize_default_values()
        cls.handler = ARQDataTypeHandler(cls.ctx)
        cls.msg_db = DatabaseManagerMessages(cls.ctx)
        cls.enc_db = DatabaseManagerEncryption(cls.ctx)
        cls.stations = DatabaseManagerStations(cls.ctx)
        config = cls.ctx.config_manager.config["STATION"]
        cls.mycall = f"{config['mycall']}-{config['myssid']}"

    @classmethod
    def tearDownClass(cls):
        cls.ctx.shutdown()

    def setUp(self):
        while not self.ctx.TESTMODE_EVENTS.empty():
            self.ctx.TESTMODE_EVENTS.get_nowait()

    def key_required_events(self):
        events = []
        while True:
            try:
                ev = self.ctx.TESTMODE_EVENTS.get_nowait()
            except queue.Empty:
                return events
            if ev.get("type") == "encryption" and ev.get("status") == "key_required":
                events.append(ev)

    def encrypt_for(self, callsign, plaintext_payload, hex_key=HEX_KEY):
        """Encrypts a payload as the remote station would."""
        self.ctx.station_keys.set(callsign, encryption.parse_key(hex_key))
        data, type_byte = self.handler.prepare(plaintext_payload, ARQ_SESSION_TYPES.p2pmsg_zlib_aesgcm, callsign)
        self.ctx.station_keys.remove(callsign)
        return data, type_byte

    def test_prepare_needs_key(self):
        with self.assertRaises(encryption.KeyMissingError):
            self.handler.prepare(bytearray(b"x"), ARQ_SESSION_TYPES.p2pmsg_zlib_aesgcm, "NOKEY1-0")

    def test_receive_with_key(self):
        remote = "EN1AAA-0"
        payload = message_payload(f"{remote}_{self.mycall}_2026-10-23T10:00:00+00:00", remote, self.mycall)
        data, type_byte = self.encrypt_for(remote, payload)
        self.assertEqual(type_byte, ARQ_SESSION_TYPES.p2pmsg_zlib_aesgcm.value)
        self.assertNotIn(b"secret hello", bytes(data))

        self.ctx.station_keys.set(remote, encryption.parse_key(HEX_KEY))
        try:
            result = self.handler.dispatch(type_byte, data, statistics={}, dxcall=remote)
        finally:
            self.ctx.station_keys.remove(remote)
        self.assertEqual(json.loads(result)["body"], "secret hello")
        stored = self.msg_db.get_message_by_id(json.loads(result)["id"])
        self.assertEqual(stored["body"], "secret hello")
        self.assertTrue(stored["encrypted"])
        self.assertEqual(self.enc_db.count_pending(remote), 0)

    def test_receive_without_key_then_enter_key(self):
        remote = "EN2AAA-0"
        msg_id = f"{remote}_{self.mycall}_2026-10-23T11:00:00+00:00"
        data, type_byte = self.encrypt_for(remote, message_payload(msg_id, remote, self.mycall))

        self.assertIsNone(self.handler.dispatch(type_byte, data, statistics={"total_bytes": 1}, dxcall=remote))
        self.assertEqual(self.enc_db.count_pending(remote), 1)
        self.assertIsNone(self.msg_db.get_message_by_id(msg_id))
        events = self.key_required_events()
        self.assertEqual([(e["callsign"], e["reason"]) for e in events], [(remote, "receive")])

        # a wrong key is rejected and not stored
        with self.assertRaises(HTTPException) as cm:
            asyncio.run(put_station_encryption_key(remote, {"key": OTHER_HEX_KEY}, self.ctx))
        self.assertEqual(cm.exception.status_code, 400)
        self.assertFalse(self.ctx.station_keys.has(remote))
        self.assertEqual(self.enc_db.count_pending(remote), 1)

        response = asyncio.run(put_station_encryption_key(remote, {"key": HEX_KEY}, self.ctx))
        result = json.loads(response.body)
        self.assertEqual(result["decrypted"], 1)
        self.assertTrue(result["key_loaded"])
        self.assertEqual(result["pending_received"], 0)
        stored = self.msg_db.get_message_by_id(msg_id)
        self.assertEqual(stored["body"], "secret hello")
        self.assertTrue(stored["encrypted"])
        self.assertEqual(stored["statistics"]["total_bytes"], 1)
        self.ctx.station_keys.remove(remote)

    def test_receive_with_wrong_key_keeps_message(self):
        remote = "EN3AAA-0"
        msg_id = f"{remote}_{self.mycall}_2026-10-23T12:00:00+00:00"
        data, type_byte = self.encrypt_for(remote, message_payload(msg_id, remote, self.mycall))
        self.ctx.station_keys.set(remote, encryption.parse_key(OTHER_HEX_KEY))
        try:
            self.assertIsNone(self.handler.dispatch(type_byte, data, statistics={}, dxcall=remote))
        finally:
            self.ctx.station_keys.remove(remote)
        self.assertEqual(self.enc_db.count_pending(remote), 1)
        self.assertEqual([e["reason"] for e in self.key_required_events()], ["wrong_key"])

    def test_send_waits_for_key(self):
        remote = "EN4AAA-0"
        response = asyncio.run(patch_station_encryption(remote, {"enabled": True}, self.ctx))
        self.assertTrue(json.loads(response.body)["enabled"])
        self.assertTrue(self.stations.is_encryption_enabled(remote))

        command = command_message_send.SendMessageCommand(self.ctx, {"destination": remote, "body": "hold me"})
        msg_id = command.message.id
        self.assertEqual(self.msg_db.get_message_by_id(msg_id)["status"], "key_required")
        self.assertEqual([(e["callsign"], e["reason"]) for e in self.key_required_events()], [(remote, "send")])

        status = json.loads(asyncio.run(get_station_encryption(remote, self.ctx)).body)
        self.assertEqual(status["waiting_to_send"], 1)
        self.assertFalse(status["key_loaded"])

        result = json.loads(asyncio.run(put_station_encryption_key(remote, {"key": HEX_KEY}, self.ctx)).body)
        self.assertEqual(result["requeued"], 1)
        self.assertEqual(result["fingerprint"], encryption.key_fingerprint(bytes.fromhex(HEX_KEY)))
        self.assertEqual(self.msg_db.get_message_by_id(msg_id)["status"], "queued")

        result = json.loads(asyncio.run(delete_station_encryption_key(remote, self.ctx)).body)
        self.assertFalse(result["key_loaded"])
        self.assertIsNone(result["fingerprint"])

        # turning encryption off: new messages are queued normally again
        asyncio.run(patch_station_encryption(remote, {"enabled": False}, self.ctx))
        command = command_message_send.SendMessageCommand(self.ctx, {"destination": remote, "body": "plain"})
        self.assertEqual(self.msg_db.get_message_by_id(command.message.id)["status"], "queued")
        self.msg_db.update_message(msg_id, {"status": "transmitted"})
        self.msg_db.update_message(command.message.id, {"status": "transmitted"})

    def test_encryption_is_off_by_default(self):
        status = json.loads(asyncio.run(get_station_encryption("EN5AAA-0", self.ctx)).body)
        self.assertEqual(status["callsign"], "EN5AAA-0")
        self.assertFalse(status["enabled"])
        self.assertFalse(status["key_loaded"])

    def test_api_validation(self):
        with self.assertRaises(HTTPException) as cm:
            asyncio.run(patch_station_encryption("EN6AAA-0", {"enabled": "yes"}, self.ctx))
        self.assertEqual(cm.exception.status_code, 400)
        with self.assertRaises(HTTPException) as cm:
            asyncio.run(put_station_encryption_key("EN6AAA-0", {"key": "short"}, self.ctx))
        self.assertEqual(cm.exception.status_code, 400)
        with self.assertRaises(HTTPException) as cm:
            asyncio.run(get_station_encryption("not a callsign!", self.ctx))
        self.assertEqual(cm.exception.status_code, 400)


class TestDatabaseMigration(unittest.TestCase):
    def test_new_columns_added_to_old_database(self):
        """A version 1 database gets the encryption columns and table on startup."""
        import sqlite3

        db_path = os.path.join(os.path.dirname(os.environ["FREEDATA_DATABASE"]), "migration-v1.db")
        conn = sqlite3.connect(db_path)
        conn.executescript(
            """
            CREATE TABLE station (callsign VARCHAR PRIMARY KEY, checksum VARCHAR, location JSON, info JSON);
            CREATE TABLE config (db_variable VARCHAR PRIMARY KEY, db_version VARCHAR);
            INSERT INTO station VALUES ('OLD1AA-0', 'abc', NULL, NULL);
            INSERT INTO config VALUES ('database_version', '1');
            """
        )
        conn.commit()
        conn.close()

        previous = os.environ["FREEDATA_DATABASE"]
        os.environ["FREEDATA_DATABASE"] = db_path
        try:
            ctx = AppContext(testenv.config_path())
            ctx.message_system_db_manager.check_database_version()
            stations = DatabaseManagerStations(ctx)
            self.assertFalse(stations.is_encryption_enabled("OLD1AA-0"))
            self.assertTrue(stations.set_encryption_enabled("OLD1AA-0", True))
            self.assertTrue(stations.get_station("OLD1AA-0")["encryption_enabled"])
            self.assertEqual(DatabaseManagerEncryption(ctx).count_pending("OLD1AA-0"), 0)
        finally:
            os.environ["FREEDATA_DATABASE"] = previous
            ctx.shutdown()


if __name__ == "__main__":
    unittest.main()
