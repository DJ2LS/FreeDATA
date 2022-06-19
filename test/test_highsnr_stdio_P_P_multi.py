#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test small multiple-burst messages over a high quality simulated audio channel.

Legacy test for sending / receiving frames through the codec2 modem
and back through on the other station. Data injection initiates directly into
codec2 API. Tests all three codec2 data frames simultaneously.

Can be invoked from CMake, pytest, coverage or directly.

Uses util_multimode_tx.py and util_multimode_tx in separate processeses to perform
the audio tests.
"""

# pylint: disable=global-statement, invalid-name, unused-import

import contextlib
import multiprocessing
import os
import subprocess
import sys
import time

import pytest

BURSTS = 1
FRAMESPERBURST = 1
TESTFRAMES = 3

with contextlib.suppress(KeyError):
    BURSTS = int(os.environ["BURSTS"])
with contextlib.suppress(KeyError):
    FRAMESPERBURST = int(os.environ["FRAMESPERBURST"])
with contextlib.suppress(KeyError):
    TESTFRAMES = int(os.environ["TESTFRAMES"])

# For some reason, sometimes, this test requires the current directory to be `test`.
# Try to adapt dynamically. I still want to figure out why but as a workaround,
# I'm not completely dissatisfied.
if os.path.exists("test"):
    os.chdir("test")


def t_HighSNR_P_P_Multi(bursts: int, frames_per_burst: int):
    """
    Test a high signal-to-noise ratio path with DATAC0, DATAC1 and DATAC3.

    :param bursts: Number of bursts
    :type bursts: int
    :param frames_per_burst: Number of frames transmitted per burst
    :type frames_per_burst: int
    """
    # Facilitate running from main directory as well as inside test/
    tx_side = "util_multimode_tx.py"
    rx_side = "util_multimode_rx.py"
    if os.path.exists("test") and os.path.exists(os.path.join("test", tx_side)):
        tx_side = os.path.join("test", tx_side)
        rx_side = os.path.join("test", rx_side)
        os.environ["PYTHONPATH"] += ":."

    print(f"{tx_side=} / {rx_side=}")

    with subprocess.Popen(
        args=[
            "python3",
            tx_side,
            "--delay",
            "500",
            "--framesperburst",
            str(frames_per_burst),
            "--bursts",
            str(bursts),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as transmit:

        with subprocess.Popen(
            args=[
                "python3",
                rx_side,
                "--framesperburst",
                str(frames_per_burst),
                "--bursts",
                str(bursts),
                "--timeout",
                "20",
            ],
            stdin=transmit.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as receive:
            assert receive.stdout
            lastline = "".join(
                [
                    str(line, "UTF-8")
                    for line in receive.stdout.readlines()
                    if "DATAC" in str(line, "UTF-8")
                ]
            )
            assert f"DATAC0: {bursts}/{frames_per_burst * bursts}" in lastline
            assert f"DATAC1: {bursts}/{frames_per_burst * bursts}" in lastline
            assert f"DATAC3: {bursts}/{frames_per_burst * bursts}" in lastline
            print(lastline)


# @pytest.mark.parametrize("bursts", [BURSTS, 2, 3])
# @pytest.mark.parametrize("frames_per_burst", [FRAMESPERBURST, 2, 3])
@pytest.mark.parametrize("bursts", [BURSTS])
@pytest.mark.parametrize("frames_per_burst", [FRAMESPERBURST])
def test_HighSNR_P_P_multi(bursts: int, frames_per_burst: int):
    proc = multiprocessing.Process(
        target=t_HighSNR_P_P_Multi,
        args=[bursts, frames_per_burst],
        daemon=True,
    )

    proc.start()

    # Set timeout
    timeout = time.time() + 5

    while time.time() < timeout:
        time.sleep(0.1)

    if proc.is_alive():
        proc.terminate()
        assert 0, "Timeout waiting for test to complete."

    proc.join()
    proc.terminate()

    assert proc.exitcode == 0
    proc.close()


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-v", "-s", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
