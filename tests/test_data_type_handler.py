import sys
import unittest
import queue

from freedata_server.context import AppContext
from freedata_server.arq_data_type_handler import ARQDataTypeHandler, ARQ_SESSION_TYPES


class TestDispatcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = AppContext("freedata_server/config.ini.example")
        cls.event_manager = cls.ctx.event_manager
        cls.state_manager = cls.ctx.state_manager
        cls.arq_data_type_handler = ARQDataTypeHandler(cls.ctx)

    @classmethod
    def tearDownClass(cls):
        # Clean shutdown after all tests
        cls.ctx.shutdown()

    def test_data_type_handler_raw(self):
        example_data = b"Hello FreeDATA!"
        formatted_data, type_byte = self.arq_data_type_handler.prepare(
            example_data, ARQ_SESSION_TYPES.raw
        )
        dispatched_data = self.arq_data_type_handler.dispatch(
            type_byte, formatted_data, statistics={}
        )
        self.assertEqual(example_data, dispatched_data)

    def test_data_type_handler_lzma(self):
        example_data = b"Hello FreeDATA! " * 50
        formatted_data, type_byte = self.arq_data_type_handler.prepare(
            example_data, ARQ_SESSION_TYPES.raw_lzma
        )
        self.assertLess(len(formatted_data), len(example_data), "LZMA komprimiert nicht richtig!")
        dispatched_data = self.arq_data_type_handler.dispatch(
            type_byte, formatted_data, statistics={}
        )
        self.assertEqual(example_data, dispatched_data)

    def test_data_type_handler_gzip(self):
        example_data = b"Hello FreeDATA! " * 50
        formatted_data, type_byte = self.arq_data_type_handler.prepare(
            example_data, ARQ_SESSION_TYPES.raw_gzip
        )
        self.assertLess(len(formatted_data), len(example_data), "GZIP komprimiert nicht richtig!")
        dispatched_data = self.arq_data_type_handler.dispatch(
            type_byte, formatted_data, statistics={}
        )
        self.assertEqual(example_data, dispatched_data)


if __name__ == "__main__":
    unittest.main()
