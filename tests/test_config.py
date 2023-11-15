import unittest
from modem import config

class TestConfigMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = config.CONFIG('modem/config.ini')

    def test_config_exists(self):
        c = config.CONFIG('modem/config.ini')
        self.assertTrue(c.config_exists())

        c = config.CONFIG('modem/nonexistant.ini')
        self.assertFalse(c.config_exists())

    def test_read(self):
        data = self.config.read()
        self.assertIsInstance(data, dict)

        self.assertIn('STATION', data.keys())
        self.assertIn('AUDIO', data.keys())
        self.assertIn('RADIO', data.keys())

    def test_write(self):
        c = self.config.read()       
        oldcall = c['STATION']['mycall']
        newcall = 'T1CALL'
        self.assertNotEqual(oldcall, newcall)

        c['STATION']['mycall'] = newcall
        new_conf = self.config.write(c)        
        self.assertEqual(new_conf['STATION']['mycall'], newcall)
        c = self.config.read()       
        self.assertEqual(c['STATION']['mycall'], newcall)

        # put it back as it was
        c['STATION']['mycall'] = oldcall
        last_conf = self.config.write(c)
        self.assertEqual(last_conf['STATION']['mycall'], oldcall)

    def test_validate_data(self):
        data = {'STATION': {'ssid_list': "abc"}}
        with self.assertRaises(ValueError):
            self.config.validate(data)

        data = {'STATION': {'ssid_list': [1, 2, 3]}}
        self.assertIsNone(self.config.validate(data))
        

if __name__ == '__main__':
    unittest.main()
