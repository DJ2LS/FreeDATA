#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import multiprocessing
import os
import sys
import time

import pytest

# pylint: disable=wrong-import-position
sys.path.insert(0, "..")
sys.path.insert(0, "../tnc")
sys.path.insert(0, "test")
import util_tnc_IRS as irs
import util_tnc_ISS as iss


# These do not update static.INFO:
#   "CONNECT", "SEND_TEST_FRAME"
# This test is currently a little inconsistent.
@pytest.mark.flaky(reruns=3)
@pytest.mark.parametrize("command", ["CQ", "PING", "BEACON"])
def test_tnc(command):

    iss_proc = multiprocessing.Process(target=iss.t_arq_iss, args=[command])
    irs_proc = multiprocessing.Process(target=irs.t_arq_irs, args=[command])
    # print("Starting threads.")
    iss_proc.start()
    irs_proc.start()

    time.sleep(12)

    # print("Terminating threads.")
    irs_proc.terminate()
    iss_proc.terminate()
    irs_proc.join()
    iss_proc.join()

    for idx in range(2):
        try:
            os.unlink(f"/tmp/hfchannel{idx+1}")
        except FileNotFoundError as fnfe:
            print(f"Unlinking pipe: {fnfe}")

    assert iss_proc.exitcode == 0, f"Transmit side failed test. {iss_proc}"
    assert irs_proc.exitcode == 0, f"Receive side failed test. {irs_proc}"


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-s", "-v", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
