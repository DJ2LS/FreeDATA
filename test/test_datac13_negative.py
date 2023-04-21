#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Negative tests for datac13 frames.

@author: kronenpj
"""

import contextlib
import multiprocessing
import os
import sys
import threading
import time
import zlib

import helpers
import log_handler
import pytest
import structlog

try:
    import test.util_datac13_negative as util
except ImportError:
    import util_datac13_negative as util


STATIONS = ["AA2BB", "ZZ9YY"]

PIPE_THREAD_RUNNING = True


def parameters() -> dict:
    # Construct message to start beacon.
    beacon_data = {"type": "command", "command": "start_beacon", "parameter": "-5"}
    # Construct message to start ping.
    ping_data = {"type": "ping", "command": "ping", "dxcallsign": ""}
    connect_data = {"type": "arq", "command": "connect", "dxcallsign": ""}
    stop_data = {"type": "arq", "command": "stop_transmission", "dxcallsign": "DD5GG-3"}

    beacon_timeout = 1
    ping_timeout = 1
    connect_timeout = 1
    stop_timeout = 1

    beacon_tx_check = '"status":"Failed"'
    ping_tx_check = '"ping","status":"Failed"'
    connect_tx_check = '"status":"Failed"'
    stop_tx_check = '"status":"stopped"'

    beacon_rx_check = '"beacon":"received"'
    ping_rx_check = '"ping":"received"'
    connect_rx_check = '"connect":"received"'
    stop_rx_check = '"status":"stopped"'

    beacon_final_tx_check = [beacon_tx_check]
    ping_final_tx_check = [ping_tx_check]
    connect_final_tx_check = [connect_tx_check]
    stop_final_tx_check = [stop_tx_check]

    beacon_final_rx_check = [beacon_rx_check]
    ping_final_rx_check = [ping_rx_check]
    connect_final_rx_check = [connect_rx_check]
    stop_final_rx_check = [stop_rx_check]

    return {
        "beacon": (
            beacon_data,
            beacon_timeout,
            beacon_tx_check,
            beacon_rx_check,
            beacon_final_tx_check,
            beacon_final_rx_check,
        ),
        "connect": (
            connect_data,
            connect_timeout,
            connect_tx_check,
            connect_rx_check,
            connect_final_tx_check,
            connect_final_rx_check,
        ),
        "ping": (
            ping_data,
            ping_timeout,
            ping_tx_check,
            ping_rx_check,
            ping_final_tx_check,
            ping_final_rx_check,
        ),
        "stop": (
            stop_data,
            stop_timeout,
            stop_tx_check,
            stop_rx_check,
            stop_final_tx_check,
            stop_final_rx_check,
        ),
    }


def locate_data_with_crc(source_list: list, text: str, data: bytes, frametype: str):
    """Try to locate data in source_list."""
    log = structlog.get_logger("locate_data_with_crc")

    if data in source_list:
        with contextlib.suppress():
            data = zlib.decompress(data[2:])
        log.info(f"analyze_results: {text} no CRC", _frametype=frametype, data=data)
    elif data + helpers.get_crc_8(data) in source_list:
        with contextlib.suppress(zlib.error):
            data = zlib.decompress(data[2:-1])
        log.info(f"analyze_results: {text} CRC 8", _frametype=frametype, data=data)
    elif data + helpers.get_crc_16(data) in source_list:
        with contextlib.suppress(zlib.error):
            data = zlib.decompress(data[2:-2])
        log.info(f"analyze_results: {text} CRC16", _frametype=frametype, data=data)
    elif data + helpers.get_crc_24(data) in source_list:
        with contextlib.suppress(zlib.error):
            data = zlib.decompress(data[2:-3])
        log.info(f"analyze_results: {text} CRC24", _frametype=frametype, data=data)
    elif data + helpers.get_crc_32(data) in source_list:
        with contextlib.suppress(zlib.error):
            data = zlib.decompress(data[2:-4])
        log.info(f"analyze_results: {text} CRC32", _frametype=frametype, data=data)
    else:
        log.info(
            f"analyze_results: {text} not received:",
            _frame=frametype,
            data=data,
        )


def analyze_results(station1: list, station2: list, call_list: list):
    """Examine the information retrieved from the sub-processes."""
    # Data in these lists is either a series of bytes of received data,
    # or a bytearray of transmitted data from the station.
    log = structlog.get_logger("analyze_results")

    # Check that each station's transmitted data was received by the other.
    for s1, s2, text in [
        (station1, station2, call_list[0]),
        (station2, station1, call_list[1]),
    ]:
        for s1_item in s1:
            if not isinstance(s1_item, list):
                continue
            data = bytes(s1_item[0])
            frametypeno = int.from_bytes(data[:1], "big")
            # frametype = static.FRAME_TYPE(frametypeno).name
            frametype = str(frametypeno)
            s1_crc = helpers.decode_call(helpers.bytes_to_callsign(data[1:4]))
            s2_crc = helpers.decode_call(helpers.bytes_to_callsign(data[2:5]))
            log.info(
                "analyze_results: callsign CRCs:",
                tx_station=text,
                s1_crc=s1_crc,
                s2_crc=s2_crc,
            )

            locate_data_with_crc(s2, text, data, frametype)


# @pytest.mark.parametrize("frame_type", ["beacon", "connect", "ping"])
@pytest.mark.parametrize("frame_type", ["ping", "stop"])
def test_datac13_negative(frame_type: str, tmp_path):
    log_handler.setup_logging(filename=tmp_path / "test_datac13", level="DEBUG")
    log = structlog.get_logger("test_datac13")

    s1_data = []
    s2_data = []

    def recv_data(buffer: list, pipe):
        while PIPE_THREAD_RUNNING:
            if pipe.poll(0.1):
                buffer.append(pipe.recv())
            else:
                time.sleep(0.1)

    def recv_from_pipes(s1_rx, s1_pipe, s2_rx, s2_pipe) -> list:
        processes = [
            threading.Thread(target=recv_data, args=(s1_rx, s1_pipe)),
            threading.Thread(target=recv_data, args=(s2_rx, s2_pipe)),
        ]
        for item in processes:
            item.start()

        return processes

    # This sufficiently separates the two halves of the test. This is needed
    # because both scripts change global state. They would conflict if running in
    # the same process.
    from_s1, s1_send = multiprocessing.Pipe()
    from_s2, s2_send = multiprocessing.Pipe()
    proc = [
        multiprocessing.Process(
            target=util.t_datac13_1,
            args=(
                s1_send,
                STATIONS[0],
                STATIONS[1],
                parameters()[frame_type],
                tmp_path,
            ),
            daemon=True,
        ),
        multiprocessing.Process(
            target=util.t_datac13_2,
            args=(
                s2_send,
                STATIONS[1],
                STATIONS[0],
                parameters()[frame_type],
                tmp_path,
            ),
            daemon=True,
        ),
    ]

    pipe_receivers = recv_from_pipes(s1_data, from_s1, s2_data, from_s2)
    # log.debug("Creating ")
    # print("Starting threads.")
    for p_item in proc:
        p_item.start()

    # This relies on each process exiting when its job is complete!

    # print("Waiting for threads to exit.")
    for p_item in proc:
        p_item.join()

    global PIPE_THREAD_RUNNING  # pylint: disable=global-statement
    PIPE_THREAD_RUNNING = False
    for pipe_recv in pipe_receivers:
        pipe_recv.join()

    for idx in range(2):
        try:
            os.unlink(tmp_path / f"hfchannel{idx+1}")
        except FileNotFoundError as fnfe:
            log.debug(f"Unlinking pipe: {fnfe}")

    for p_item in proc:
        assert p_item.exitcode == 0
        # p_item.close()  # Python 3.7+ only
        p_item.terminate()
        p_item.join()

    analyze_results(s1_data, s2_data, STATIONS)


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-s", "-v", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
