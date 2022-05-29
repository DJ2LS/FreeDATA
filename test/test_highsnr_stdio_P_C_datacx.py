"""
Tests a high signal-to-noise ratio path with codec2 data formats using codec2 to receive.
"""

# pylint: disable=global-statement, invalid-name, unused-import

import glob
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
@pytest.mark.parametrize("mode", ["datac0", "datac1", "datac3"])
def test_HighSNR_P_C_DATACx(bursts: int, frames_per_burst: int, mode: str):
    """
    Test a high signal-to-noise ratio path with DATAC0.

    :param bursts: Number of bursts
    :type bursts: str
    :param frames_per_burst: Number of frames transmitted per burst
    :type frames_per_burst: str
    :param testframes: Number of test frames to transmit
    :type testframes: str
    """
    # Facilitate running from main directory as well as inside test/
    rx_side = "freedv_data_raw_rx"
    _rxpath = (
        os.path.join("..", "tnc")
        if os.path.exists(os.path.join("..", "tnc"))
        else "tnc"
    )
    _rxpaths = glob.glob(rf"{_rxpath}/**/{rx_side}", recursive=True)
    for path in _rxpaths:
        rx_side = path
        break

    tx_side = "util_tx.py"
    if os.path.exists("test") and os.path.exists(os.path.join("test", tx_side)):
        tx_side = os.path.join("test", tx_side)
        os.environ["PYTHONPATH"] += ":."

    print(f"{tx_side=} / {rx_side=}")

    with subprocess.Popen(
        args=[
            "python3",
            tx_side,
            "--mode",
            mode,
            "--delay",
            "500",
            "--framesperburst",
            f"{frames_per_burst}",
            "--bursts",
            f"{bursts}",
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
                "48000",
                "-c",
                "1",
                "-",
                "-t",
                ".s16",
                "-r",
                "8000",
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
                    rx_side,
                    mode,
                    "-",
                    "-",
                    "--framesperburst",
                    str(frames_per_burst),
                ],
                stdin=sox_filter.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            ) as receive:

                with subprocess.Popen(
                    args=[
                        "hexdump",
                        "-C",
                    ],
                    stdin=receive.stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                ) as hexdump:
                    assert hexdump.stdout
                    lastline = "".join(
                        [
                            str(line, "UTF-8")
                            for line in hexdump.stdout.readlines()
                            if "HELLO" in str(line, "UTF-8")
                        ]
                    )
                    assert "HELLO WORLD!" in lastline
                    print(lastline)


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-v", "-s", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
