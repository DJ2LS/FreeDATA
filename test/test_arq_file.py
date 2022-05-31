#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

import multiprocessing
import sys
import threading
import time
from pprint import pformat

import pytest
import structlog

# pylint: disable=wrong-import-position
sys.path.insert(0, "..")
sys.path.insert(0, "../tnc")
sys.path.insert(0, "test")
import helpers
import log_handler
import util_arq_chat_file_1 as util1
import util_arq_chat_file_2 as util2

log_handler.setup_logging("/tmp/test")

STATIONS = ["AA2BB", "ZZ9YY"]

bytes_out = b'{"dt":"f","fn":"zeit.txt","ft":"text\\/plain","d":"data:text\\/plain;base64,MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=","crc":"123123123"}'

messages = ["This is a test chat."]
PIPE_THREAD_RUNNING = True


def analyze_results(station1: list, station2: list):
    """Examine the information retrieved from the sub-processes."""
    # Data in these lists is either a series of bytes of received data,
    # or a bytearray of transmitted data from the station.
    log = structlog.get_logger("analyze_results")

    for s1, s2, text in [(station1, station2, "S1"), (station2, station1, "S2")]:
        for item in s1:
            if not isinstance(item, list):
                continue
            data = bytes(item[0])
            frametype = int.from_bytes(data[:1], "big")
            call1 = helpers.decode_call(helpers.bytes_to_callsign(data[1:4]))
            call2 = helpers.decode_call(helpers.bytes_to_callsign(data[2:5]))
            log.debug("analyze_results: callsigns:", call1=call1, call2=call2)

            if data in s2:
                log.debug(f"analyze_results: {text} no CRC", _frame=frametype, data=data)
            elif data + helpers.get_crc_16(data) in s2:
                log.debug(f"analyze_results: {text} CRC16", _frame=frametype, data=data)
            elif data + helpers.get_crc_24(data) in s2:
                log.debug(f"analyze_results: {text} CRC24", _frame=frametype, data=data)
            else:
                log.debug(f"analyze_results: {text} not received:", _frame=frametype, data=data)

    # log.debug("Everything")
    # log.debug("S1:", s1=pformat(s1))
    # log.debug("S2:", s2=pformat(s2))


# @pytest.mark.parametrize("freedv_mode", ["datac0", "datac1", "datac3"])
# @pytest.mark.parametrize("n_frames_per_burst", [1, 2, 3])
@pytest.mark.parametrize("freedv_mode", ["datac3"])
@pytest.mark.parametrize("n_frames_per_burst", [2])
@pytest.mark.parametrize("lowbwmode", [False, True])
def test_arq_short(freedv_mode: str, n_frames_per_burst: int, lowbwmode: bool):
    log = structlog.get_logger("test_arq_short")

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
            target=util1.t_highsnr_arq_short_station1,
            args=(
                s1_send,
                freedv_mode,
                n_frames_per_burst,
                STATIONS[0],
                STATIONS[1],
                messages[0],
                lowbwmode,
            ),
            daemon=True,
        ),
        multiprocessing.Process(
            target=util2.t_highsnr_arq_short_station2,
            args=(
                s2_send,
                freedv_mode,
                n_frames_per_burst,
                STATIONS[1],
                STATIONS[0],
                messages[0],
                lowbwmode,
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

    # print(f"\n{proc.exitcode=}")
    for p_item in proc:
        assert p_item.exitcode == 0
        p_item.close()

    analyze_results(s1_data, s2_data)


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-s", "-v", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
