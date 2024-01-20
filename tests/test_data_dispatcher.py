import sys
sys.path.append('modem')

import unittest
from data_dispatcher import DataDispatcher

class TestDispatcher(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.data_dispatcher = DataDispatcher()


    def testEncapsulator(self):
        message_type = "p2pmsg"
        message_data = {"message": "Hello, P2P World!"}

        encapsulated = self.data_dispatcher.encapsulate(message_data, message_type)
        type, decapsulated = self.data_dispatcher.decapsulate(encapsulated.encode('utf-8'))
        self.assertEqual(type, message_type)
        self.assertEqual(decapsulated, message_data)

    def testDispatcher(self):
        message_type = "test"
        message_data = {"message": "Hello, P2P World!"}

        encapsulated = self.data_dispatcher.encapsulate(message_data, message_type)
        self.data_dispatcher.dispatch(encapsulated.encode('utf-8'))



if __name__ == '__main__':
    unittest.main()
