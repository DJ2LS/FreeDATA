import sys
sys.path.append('modem')

import unittest
from arq_data_type_handler import ARQDataTypeHandler

class TestDispatcher(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.arq_data_type_handler = ARQDataTypeHandler()


    def testDataTypeHandlerRaw(self):
        # Example usage
        example_data = b"Hello FreeDATA!"
        formatted_data, type_byte = self.arq_data_type_handler.prepare(example_data, "raw")
        dispatched_data = self.arq_data_type_handler.dispatch(type_byte, formatted_data)
        self.assertEqual(example_data, dispatched_data)

    def testDataTypeHandlerLZMA(self):
        # Example usage
        example_data = b"Hello FreeDATA!"
        formatted_data, type_byte = self.arq_data_type_handler.prepare(example_data, "raw_lzma")
        dispatched_data = self.arq_data_type_handler.dispatch(type_byte, formatted_data)
        self.assertEqual(example_data, dispatched_data)

    def testDataTypeHandlerGZIP(self):
        # Example usage
        example_data = b"Hello FreeDATA!"
        formatted_data, type_byte = self.arq_data_type_handler.prepare(example_data, "raw_gzip")
        dispatched_data = self.arq_data_type_handler.dispatch(type_byte, formatted_data)
        self.assertEqual(example_data, dispatched_data)


if __name__ == '__main__':
    unittest.main()
