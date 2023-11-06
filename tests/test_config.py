import unittest
from modem import config

class TestConfigMethods(unittest.TestCase):

    def test_config_exists(self):
        c = config.CONFIG('modem/config.ini')
        self.assertTrue(c.config_exists())

        c = config.CONFIG('modem/nonexistant.ini')
        self.assertFalse(c.config_exists())


    def test_validate_data(self):
        c = config.CONFIG('modem/config.ini')
        data = {'NETWORK': {'modemport': "abc"}}
        with self.assertRaises(ValueError):
            c.validate(data)

        data = {'NETWORK': {'modemport': "3000"}}
        self.assertIsNone(c.validate(data))


if __name__ == '__main__':
    unittest.main()
