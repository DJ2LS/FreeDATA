"""
Tests for the FreeDATA TNC state machine.
"""

# pylint: disable=global-statement, invalid-name, unused-import

import os
import subprocess
import sys

import pytest

try:
    BURSTS = int(os.environ["BURSTS"])
    FRAMESPERBURST = int(os.environ["FRAMESPERBURST"])
    TESTFRAMES = int(os.environ["TESTFRAMES"])
except KeyError:
    BURSTS = 1
    FRAMESPERBURST = 1
    TESTFRAMES = 3


@pytest.mark.parametrize("bursts", [BURSTS, 2, 3])
@pytest.mark.parametrize("frames_per_burst", [FRAMESPERBURST, 2, 3])
@pytest.mark.parametrize("testframes", [TESTFRAMES, 2, 1])
@pytest.mark.parametrize("mode", ["datac0", "datac1", "datac3"])
def test_HighSNR_P_P_DATACx(
    bursts: int, frames_per_burst: int, testframes: int, mode: str
):
    """
    Test a high signal-to-noise ratio path with DATAC0.

    :param bursts: Number of bursts
    :type bursts: str
    :param frames_per_burst: Number of frames transmitted per burst
    :type frames_per_burst: str
    :param testframes: Number of test frames to transmit
    :type testframes: str
    """
    tx_side = "freedv_data_raw_tx"

    # Facilitate running from main directory as well as inside test/
    rx_side = "test_rx.py"
    if os.path.exists("test") and os.path.exists(os.path.join("test", rx_side)):
        rx_side = os.path.join("test", rx_side)
        os.environ["PYTHONPATH"] += ":."

    with subprocess.Popen(
        args=[
            tx_side,
            mode,
            "--testframes",
            f"{testframes}",
            "--bursts",
            f"{bursts}",
            "--framesperburst",
            f"{frames_per_burst}",
            "/dev/zero",
            "-",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as transmit:

        with subprocess.Popen(
            args=[
                "sox",
                "-t",
                ".s16",
                "-r",
                "8000",
                "-c",
                "1",
                "-",
                "-t",
                ".s16",
                "-r",
                "48000",
                "-c",
                "1",
                "-",
            ],
            stdin=transmit.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ) as sox_filter:

            with subprocess.Popen(
                args=[
                    "python3",
                    rx_side,
                    "--mode",
                    mode,
                    "--framesperburst",
                    str(frames_per_burst),
                    "--bursts",
                    str(bursts),
                ],
                stdin=sox_filter.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            ) as receive:
                assert receive.stdout
                lastline = "".join(
                    [
                        str(line, "UTF-8")
                        for line in receive.stdout.readlines()
                        if "RECEIVED " in str(line, "UTF-8")
                    ]
                )
                assert f"RECEIVED BURSTS: {bursts}" in lastline
                assert f"RECEIVED FRAMES: {frames_per_burst * bursts}" in lastline
                assert "RX_ERRORS: 0" in lastline
                print(lastline)


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-v", "-s", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
