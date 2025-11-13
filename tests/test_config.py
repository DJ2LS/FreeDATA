import os
import shutil
import tempfile
import unittest

from freedata_server import config


class DummyCtx:
    def __init__(self):
        pass


class TestConfigMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Copy example ini to a temp file so we don't overwrite the source
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "freedata_server"))
        example_path = os.path.join(base, "config.ini.example")
        cls.temp_ini = tempfile.NamedTemporaryFile(delete=False, suffix=".ini").name
        shutil.copy(example_path, cls.temp_ini)
        cls.ctx = DummyCtx()
        cls.config = config.CONFIG(cls.ctx, cls.temp_ini)

    @classmethod
    def tearDownClass(cls):
        # Remove temp file
        try:
            os.remove(cls.temp_ini)
        except OSError:
            pass

    def test_config_exists(self):
        # Should find the copied temp file
        self.assertTrue(self.config.config_exists())

    def test_read(self):
        data = self.config.read()
        self.assertIsInstance(data, dict)
        self.assertIn("STATION", data)
        self.assertIn("AUDIO", data)
        self.assertIn("RADIO", data)

    def test_write(self):
        data = self.config.read()
        old_call = data["STATION"]["mycall"]
        new_call = "T1CALL"
        self.assertNotEqual(old_call, new_call)

        # Update value and write
        data["STATION"]["mycall"] = new_call
        updated = self.config.write(data)
        self.assertEqual(updated["STATION"]["mycall"], new_call)

        # Confirm persisted
        reloaded = self.config.read()
        self.assertEqual(reloaded["STATION"]["mycall"], new_call)

        # Restore original
        reloaded["STATION"]["mycall"] = old_call
        restored = self.config.write(reloaded)
        self.assertEqual(restored["STATION"]["mycall"], old_call)

    def test_validate_data(self):
        # Invalid: ssid_list must be a list, not a string
        with self.assertRaises(ValueError):
            self.config.validate_data({"STATION": {"ssid_list": "abc"}})

        # Valid case returns None
        result = self.config.validate_data({"STATION": {"ssid_list": [1, 2, 3]}})
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
