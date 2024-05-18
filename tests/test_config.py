import sys
sys.path.append('freedata_server')
import unittest
import config

class TestConfigMethods(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.config = config.CONFIG('freedata_server/config.ini.example')

    def test_config_exists(self):
        c = config.CONFIG('freedata_server/config.ini.example')
        self.assertTrue(c.config_exists())

        #c = config.CONFIG('freedata_server/nonexistant')
        #self.assertFalse(c.config_exists())

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
            self.config.validate_data(data)

        data = {'STATION': {'ssid_list': [1, 2, 3]}}
        self.assertIsNone(self.config.validate_data(data))
        

if __name__ == '__main__':
    unittest.main()
