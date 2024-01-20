import sys
sys.path.append('modem')

import unittest
from arq_data_formatter import ARQDataFormatter
from arq_received_data_dispatcher import ARQReceivedDataDispatcher

class TestDispatcher(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_dispatcher = ARQReceivedDataDispatcher()
        cls.data_formatter = ARQDataFormatter()


    def testEncapsulator(self):
        message_type = "p2pmsg"
        message_data = {"message": "Hello, P2P World!"}

        encapsulated = self.data_formatter.encapsulate(message_data, message_type)
        type, decapsulated = self.data_formatter.decapsulate(encapsulated.encode('utf-8'))
        self.assertEqual(type, message_type)
        self.assertEqual(decapsulated, message_data)

    def testDispatcher(self):
        message_type = "test"
        message_data = {"message": "Hello, P2P World!"}

        encapsulated = self.data_formatter.encapsulate(message_data, message_type)
        self.data_dispatcher.dispatch(encapsulated.encode('utf-8'))



if __name__ == '__main__':
    unittest.main()
