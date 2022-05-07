"""
Tests for the FreeDATA TNC state machine.
"""

# pylint: disable=global-statement, invalid-name, unused-import

import os
import subprocess
import sys

import pytest

BURSTS = int(os.environ["BURSTS"])
FRAMESPERBURST = int(os.environ["FRAMESPERBURST"])


@pytest.mark.parametrize("bursts", [BURSTS, 2, 3])
@pytest.mark.parametrize("frames_per_burst", [FRAMESPERBURST, 2, 3])
def test_HighSNR_P_P_Multi(bursts: int, frames_per_burst: int):
    """
    Test a high signal-to-noise ratio path with DATAC0, DATAC1 and DATAC3.

    :param bursts: Number of bursts
    :type bursts: int
    :param frames_per_burst: Number of frames transmitted per burst
    :type frames_per_burst: int
    """
    # Facilitate running from main directory as well as inside test/
    tx_side = "test_multimode_tx.py"
    rx_side = "test_multimode_rx.py"
    if os.path.exists("test") and os.path.exists(os.path.join("test", tx_side)):
        tx_side = os.path.join("test", tx_side)
        rx_side = os.path.join("test", rx_side)
        os.environ["PYTHONPATH"] += ":."

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


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-v", "-s", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
