import sys
sys.path.append('freedata_server')

import unittest
import queue
from arq_data_type_handler import ARQDataTypeHandler, ARQ_SESSION_TYPES
from event_manager import EventManager
from state_manager import StateManager

class TestDispatcher(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.event_queue = queue.Queue()
        cls.state_queue = queue.Queue()
        cls.event_manager = EventManager([cls.event_queue])
        cls.state_manager = StateManager([cls.state_queue])
        cls.arq_data_type_handler = ARQDataTypeHandler(cls.event_manager, cls.state_manager)


    def testDataTypeHevent_managerandlerRaw(self):
        # Example usage
        example_data = b"Hello FreeDATA!"
        formatted_data, type_byte = self.arq_data_type_handler.prepare(example_data, ARQ_SESSION_TYPES.raw)
        dispatched_data = self.arq_data_type_handler.dispatch(type_byte, formatted_data, statistics={})
        self.assertEqual(example_data, dispatched_data)

    def testDataTypeHandlerLZMA(self):
        # Example usage
        example_data = b"Hello FreeDATA!"
        formatted_data, type_byte = self.arq_data_type_handler.prepare(example_data, ARQ_SESSION_TYPES.raw_lzma)
        dispatched_data = self.arq_data_type_handler.dispatch(type_byte, formatted_data, statistics={})
        self.assertEqual(example_data, dispatched_data)

    def testDataTypeHandlerGZIP(self):
        # Example usage
        example_data = b"Hello FreeDATA!"
        formatted_data, type_byte = self.arq_data_type_handler.prepare(example_data, ARQ_SESSION_TYPES.raw_gzip)
        dispatched_data = self.arq_data_type_handler.dispatch(type_byte, formatted_data, statistics={})
        self.assertEqual(example_data, dispatched_data)


if __name__ == '__main__':
    unittest.main()
