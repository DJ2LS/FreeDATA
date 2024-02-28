import unittest
from subprocess import Popen, PIPE
import shlex, os
import requests
import time
import json

# API Server integration testst
class TestIntegration(unittest.TestCase):

    process = None
    url = "http://127.0.0.1:5000"

    @classmethod
    def setUpClass(cls):
        #cmd = "flask --app modem/server run"
        cmd = "python3 modem/server.py"
        my_env = os.environ.copy()
        my_env["FREEDATA_CONFIG"] = "modem/config.ini.example"
        cls.process = Popen(shlex.split(cmd), stdin=PIPE, env=my_env)
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.process.stdin.close()
        cls.process.terminate()
        cls.process.wait()

    def test_index(self):
        r = requests.get(self.url)
        self.assertEqual(r.status_code, 200)

        data = r.json()
        self.assertEqual(data['api_version'], 1)

    def test_config_get(self):
        r = requests.get(self.url + '/config')
        self.assertEqual(r.status_code, 200)

        config = r.json()
        self.assertIsInstance(config, dict)

        self.assertIn('NETWORK', config)
        self.assertIn('STATION', config)
        self.assertIn('AUDIO', config)
        self.assertIn('MODEM', config)
        self.assertIn('TCI', config)
        self.assertIn('RADIO', config)

    def test_config_post(self):
        config = {'STATION': {'mygrid' : 'JN48ea'}}
        r = requests.post(self.url + '/config', 
                          headers={'Content-type': 'application/json'},
                          data = json.dumps(config))
        self.assertEqual(r.status_code, 200)

        r = requests.get(self.url + '/config')
        self.assertEqual(r.status_code, 200)
        config = r.json()
        self.assertEqual(config['NETWORK']['modemport'], 5000)

if __name__ == '__main__':
    unittest.main()
