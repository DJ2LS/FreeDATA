import sys
sys.path.append('freedata_server')

import unittest
from config import CONFIG
from data_frame_factory import DataFrameFactory
from codec2 import FREEDV_MODE
import helpers
from modem_frametypes import FRAME_TYPE

class TestDataFrameFactory(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_manager = CONFIG('freedata_server/config.ini.example')
        config = config_manager.read()
        cls.factory = DataFrameFactory(config)

    def testBeacon(self):
        beacon_frame = self.factory.build_beacon()
        beacon_data = self.factory.deconstruct(beacon_frame)
        self.assertEqual(beacon_data['origin'], self.factory.myfullcall.upper())
        self.assertEqual(beacon_data['gridsquare'], self.factory.mygrid.upper())

    def testPing(self):
        dxcall = "DJ2LS-3"
        ping_frame = self.factory.build_ping(dxcall)
        ping_data = self.factory.deconstruct(ping_frame)
        self.assertEqual(ping_data['origin'], self.factory.myfullcall)
        self.assertEqual(ping_data['destination_crc'], helpers.get_crc_24(dxcall).hex())

    def testARQConnect(self):
        dxcall = "DJ2LS-4"
        session_id = 123
        frame = self.factory.build_arq_session_open(dxcall, session_id, 1700, 1)
        frame_data = self.factory.deconstruct(frame)

        self.assertEqual(frame_data['origin'], self.factory.myfullcall)
        self.assertEqual(frame_data['session_id'] , session_id)

    def testCQ(self):
        frame = self.factory.build_cq()
        frame_data = self.factory.deconstruct(frame)
        self.assertEqual(frame_data['origin'], self.factory.myfullcall)
        self.assertEqual(frame_data['gridsquare'], self.factory.mygrid.upper())

    def testBurstDataFrames(self):
        session_id = 123
        offset = 40
        payload = b'Hello World!'
        frame = self.factory.build_arq_burst_frame(FREEDV_MODE.datac3, 
                                                session_id, offset, payload, 0)
        frame_data = self.factory.deconstruct(frame)
        self.assertEqual(frame_data['session_id'], session_id)
        self.assertEqual(frame_data['offset'], offset)
        data = frame_data['data'][:len(payload)]
        self.assertEqual(data, payload)

        payload = payload * 1000
        self.assertRaises(OverflowError, self.factory.build_arq_burst_frame,
            FREEDV_MODE.datac3, session_id, offset, payload, 0)
        
    def testAvailablePayload(self):
        avail = self.factory.get_available_data_payload_for_mode(FRAME_TYPE.ARQ_BURST_FRAME, FREEDV_MODE.datac3)
        self.assertEqual(avail, 119) # 128 bytes datac3 frame payload - BURST frame overhead

if __name__ == '__main__':
    unittest.main()
