import unittest
from subprocess import Popen, PIPE
import shlex
import requests
import time
import json

class TestConfigAPI(unittest.TestCase):

    process = None
    url = "http://127.0.0.1:5000"

    @classmethod
    def setUpClass(cls):
        cmd = "flask --app modem/server run"
        cls.process = Popen(shlex.split(cmd), stdin=PIPE)
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        cls.process.stdin.close()
        cls.process.terminate()
        if cls.process.wait() != 0:
            print("There were some errors closing the process.")

    def test_index(self):
        r = requests.get(self.url)
        self.assertEqual(r.status_code, 200)

        data = r.json()
        self.assertEqual(data['api_version'], 1)


if __name__ == '__main__':
    unittest.main()
