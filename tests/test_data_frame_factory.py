import os
import unittest

from freedata_server.data_frame_factory import DataFrameFactory
from freedata_server.codec2 import FREEDV_MODE
from freedata_server.config import CONFIG
from freedata_server import helpers
from freedata_server.modem_frametypes import FRAME_TYPE


# Dummy Context with config
class DummyCtx:
    def __init__(self, config_path):
        self.config_manager = CONFIG(self, config_path)


class TestDataFrameFactory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup minimal context and config
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "freedata_server"))
        example_path = os.path.join(base, "config.ini.example")
        cls.ctx = DummyCtx(example_path)
        cls.ctx.config_manager.config["STATION"]["mycall"] = "T1CALL"
        cls.ctx.config_manager.config["STATION"]["mygrid"] = "AB12aa"

        cls.factory = DataFrameFactory(cls.ctx)

    def test_build_beacon(self):
        beacon_frame = self.factory.build_beacon()
        beacon_data = self.factory.deconstruct(beacon_frame)
        self.assertEqual(beacon_data["origin"], self.factory.myfullcall.upper())
        self.assertEqual(beacon_data["gridsquare"], self.factory.mygrid.upper())

    def test_build_ping(self):
        dxcall = "DJ2LS-3"
        ping_frame = self.factory.build_ping(dxcall)
        ping_data = self.factory.deconstruct(ping_frame)
        self.assertEqual(ping_data["origin"], self.factory.myfullcall)
        self.assertEqual(ping_data["destination_crc"], helpers.get_crc_24(dxcall).hex())

    def test_build_arq_connect(self):
        dxcall = "DJ2LS-4"
        session_id = 123
        frame = self.factory.build_arq_session_open(dxcall, session_id, 1700, 1)
        frame_data = self.factory.deconstruct(frame)
        self.assertEqual(frame_data["origin"], self.factory.myfullcall)
        self.assertEqual(frame_data["session_id"], session_id)

    def test_build_cq(self):
        frame = self.factory.build_cq()
        frame_data = self.factory.deconstruct(frame)
        self.assertEqual(frame_data["origin"], self.factory.myfullcall)
        self.assertEqual(frame_data["gridsquare"], self.factory.mygrid.upper())

    def test_build_burst_data_frames(self):
        session_id = 123
        offset = 40
        payload = b"Hello World!"
        frame = self.factory.build_arq_burst_frame(FREEDV_MODE.datac3, session_id, offset, payload, 0)
        frame_data = self.factory.deconstruct(frame)
        self.assertEqual(frame_data["session_id"], session_id)
        self.assertEqual(frame_data["offset"], offset)
        extracted = frame_data["data"][: len(payload)]
        self.assertEqual(extracted, payload)

        # Check overflow condition
        oversized_payload = payload * 1000
        with self.assertRaises(OverflowError):
            self.factory.build_arq_burst_frame(FREEDV_MODE.datac3, session_id, offset, oversized_payload, 0)

    def test_available_payload(self):
        available = self.factory.get_available_data_payload_for_mode(FRAME_TYPE.ARQ_BURST_FRAME, FREEDV_MODE.datac3)
        self.assertEqual(available, 119)


if __name__ == "__main__":
    unittest.main()
