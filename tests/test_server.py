import unittest
from subprocess import Popen, PIPE
import sys
import os
import requests
import time
import json

import testenv
from freedata_server.constants import API_VERSION


# API Server integration testst
class TestIntegration(unittest.TestCase):
    process = None
    url = "http://127.0.0.1:5000"

    @classmethod
    def setUpClass(cls):
        # run with the interpreter running the tests (not whatever "python3" is on PATH)
        cmd = [sys.executable, "-m", "freedata_server.server"]
        my_env = os.environ.copy()
        my_env["FREEDATA_CONFIG"] = testenv.config_path()
        cls.process = Popen(cmd, stdin=PIPE, env=my_env)
        cls.wait_for_server(cls.url)
        time.sleep(5)

    @classmethod
    def wait_for_server(cls, url, timeout=30):
        """Wait for the server to start"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                r = requests.get(url)
                if r.status_code == 200:
                    return True
            except requests.exceptions.ConnectionError:
                time.sleep(1)
        raise RuntimeError("Server not ready after waiting for 30 seconds")

    @classmethod
    def tearDownClass(cls):
        cls.process.stdin.close()
        cls.process.terminate()
        cls.process.wait()

    def test_index(self):
        r = requests.get(self.url)
        self.assertEqual(r.status_code, 200)

        data = r.json()
        self.assertEqual(data["api_version"], API_VERSION)

    def test_config_get(self):
        r = requests.get(self.url + "/config")
        self.assertEqual(r.status_code, 200)

        config = r.json()
        self.assertIsInstance(config, dict)

        self.assertIn("NETWORK", config)
        self.assertIn("STATION", config)
        self.assertIn("AUDIO", config)
        self.assertIn("MODEM", config)
        self.assertIn("RADIO", config)

    def test_config_post(self):
        # the API requires a valid mycall and mygrid in every config update
        config = {"STATION": {"mycall": "AA1AAA", "mygrid": "JN48ea"}}
        r = requests.post(
            self.url + "/config",
            headers={"Content-type": "application/json"},
            data=json.dumps(config),
        )
        self.assertEqual(r.status_code, 200)

        r = requests.get(self.url + "/config")
        self.assertEqual(r.status_code, 200)
        config = r.json()
        self.assertEqual(config["NETWORK"]["modemport"], 5000)

    def test_message_unknown_id_404(self):
        r = requests.get(self.url + "/freedata/messages/does-not-exist")
        self.assertEqual(r.status_code, 404)

    def test_broadcast_delete_unknown_404(self):
        r = requests.delete(self.url + "/freedata/broadcasts/does-not-exist")
        self.assertEqual(r.status_code, 404)

    def test_broadcast_post_groupchat_disabled_409(self):
        # the test config (config.ini.example) has EXP.enable_groupchat = False
        payload = {
            "origin": "AA1AAA-0",
            "domain": "BB1BBB-0",
            "gridsquare": "JN48ea",
            "type": "MESSAGE",
            "priority": 1,
            "data": "aGVsbG8=",
        }
        r = requests.post(self.url + "/freedata/broadcasts", json=payload)
        self.assertEqual(r.status_code, 409)
        self.assertIn("error", r.json()["detail"])

    def test_broadcast_domain_mark_read(self):
        r = requests.get(self.url + "/freedata/broadcasts/BB1BBB-0/")
        self.assertEqual(r.status_code, 200)
        r = requests.patch(self.url + "/freedata/broadcasts/BB1BBB-0/read")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["marked_read"], 0)


if __name__ == "__main__":
    unittest.main()
