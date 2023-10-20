"""
simple Modem self tests
"""
# -*- coding: utf-8 -*-

# pylint: disable=invalid-name, line-too-long, c-extension-no-member
# pylint: disable=import-outside-toplevel, attribute-defined-outside-init
import sys
import structlog

log = structlog.get_logger("selftest")


class TEST():
    def __init__(self):
        log.info("[selftest] running self tests...")
        if self.run_tests():
            log.info("[selftest] passed -> starting Modem")
        else:
            log.error("[selftest] failed -> closing Modem")
            sys.exit(0)

    def run_tests(self):
        return bool(
            self.check_imports()
            and self.check_sounddevice()
            and self.check_helpers()
        )



    def check_imports(self):
        try:
            import argparse
            import atexit
            import multiprocessing
            import os
            import signal
            import socketserver
            import sys
            import threading
            import time
            import structlog
            import crcengine
            import ctypes
            import glob
            import enum
            import numpy
            import sounddevice
            return True
        except Exception as e:
            log.info("[selftest] [check_imports] [failed]", e=e)
            return False

    def check_sounddevice(self):
        try:
            import audio
            audio.get_audio_devices()
            return True
        except Exception as e:
            log.info("[selftest] [check_sounddevice] [failed]", e=e)
            return False

    def check_helpers(self):
        try:
            import helpers
            valid_crc24 = "f86ed0"
            if helpers.get_crc_24(b"test").hex() == valid_crc24:
                return True
            else:
                raise Exception

        except Exception as e:
            log.info("[selftest] [check_helpers] [failed]", e=e)
            return False