import sys
sys.path.append('modem')

import unittest
from config import CONFIG
import data_frame_factory

class TestDataFrameFactory(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        config_manager = CONFIG('modem/config.ini.example')
        config = config_manager.read()
        cls.factory = data_frame_factory.DataFrameFactory(config)

    def testBeacon(self):
        beacon_frame = self.factory.build_beacon()
        beacon_data = self.factory.deconstruct(beacon_frame)
        self.assertEqual(beacon_data['mycallsign'], self.factory.myfullcall.upper())
        self.assertEqual(beacon_data['mygridsquare'], self.factory.mygrid.upper())

    def testPing(self):
        dxcall = "DJ2LS-3"
        ping_frame = self.factory.build_ping(dxcall)
        ping_data = self.factory.deconstruct(ping_frame)
        self.assertEqual(ping_data['mycallsign'], self.factory.myfullcall)

if __name__ == '__main__':
    unittest.main()
