"""
Tests for the FreeDATA TNC state machine.
"""

# pylint: disable=global-statement, invalid-name, unused-import

import os
from re import sub
import subprocess
import sys

import pytest

# Replacing:
#   python3 test_multimode_tx.py --delay 500 --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS} |
#   python3 test_multimode_rx.py --framesperburst ${FRAMESPERBURST} --bursts ${BURSTS} --timeout 20")
# with python-controlled subprocesses.

BURSTS = os.environ["BURSTS"]
FRAMESPERBURST = os.environ["FRAMESPERBURST"]


def test_HighSNR_P_P_Multi():
    """
    Execute test a high signal-to-noise ratio path.

    :param mycall: Callsign of the near station
    :type mycall: str
    :param dxcall: Callsign of the far station
    :type dxcall: str
    :return: Bytearray of the requested frame
    :rtype: bytearray
    """
    with subprocess.Popen(
        args=[
            "python3",
            "test_tx.py",
            "--mode",
            "datac0",
            "--delay",
            "500",
            "--framesperburst",
            FRAMESPERBURST,
            "--bursts",
            BURSTS,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as transmit:

        with subprocess.Popen(
            args=[
                "python3",
                "test_rx.py",
                "--mode",
                "datac0",
                "--framesperburst",
                FRAMESPERBURST,
                "--bursts",
                BURSTS,
                "--timeout",
                "20",
            ],
            stdin=transmit.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as receive:
            lastline = "".join(
                [
                    str(line, "UTF-8")
                    for line in receive.stdout.readlines()
                    if "RECEIVED " in str(line, "UTF-8")
                ]
            )
            assert f"RECEIVED BURSTS: {BURSTS}" in lastline
            assert f"RECEIVED FRAMES: {int(FRAMESPERBURST) * int(BURSTS)}" in lastline
            assert "RX_ERRORS: 0" in lastline
            print(lastline)


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-v", "-s", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
