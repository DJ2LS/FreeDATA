#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
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
    import test.util_cq_1 as util1
    import test.util_cq_2 as util2
except ImportError:
    import util_cq_1 as util1
    import util_cq_2 as util2


STATIONS = ["AA2BB", "ZZ9YY"]

bytes_out = b'{"dt":"f","fn":"zeit.txt","ft":"text\\/plain","d":"data:text\\/plain;base64,MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=","crc":"123123123"}'

messages = [
    "This is a test chat...",
    "This is a much longer message, hopefully longer than each of the datac1 and datac3 frames available to use in this modem. This should be long enought, but to err on the side of completeness this will string on for many more words before coming to the long awaited conclusion. We are not at the concluding point just yet because there is still more space to be taken up in the datac3 frame. Perhaps now would be a good place to terminate this test message, but perhaps not because we need a few more bytes. Here then we stop. This compresses so well that I need more data, even more stuff than is already here and included in the unreadable diatribe below, or is it a soliloquy? MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=",
]
PIPE_THREAD_RUNNING = True


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


@pytest.mark.parametrize("freedv_mode", ["datac1", "datac3"])
@pytest.mark.parametrize("n_frames_per_burst", [1])  # Higher fpb is broken.
@pytest.mark.parametrize("message_no", range(len(messages)))
# @pytest.mark.flaky(reruns=2)
def test_cq(
    freedv_mode: str, n_frames_per_burst: int, message_no: int, tmp_path
):
    log_handler.setup_logging(filename=tmp_path / "test_cq", level="INFO")
    log = structlog.get_logger("test_cq")

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
            target=util1.t_cq1,
            args=(
                s1_send,
                freedv_mode,
                n_frames_per_burst,
                STATIONS[0],
                STATIONS[1],
                messages[message_no],
                True,  # low bandwidth mode
                tmp_path,
            ),
            daemon=True,
        ),
        multiprocessing.Process(
            target=util2.t_cq2,
            args=(
                s2_send,
                freedv_mode,
                n_frames_per_burst,
                STATIONS[1],
                STATIONS[0],
                messages[message_no],
                True,  # low bandwidth mode
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
        p_item.close()

    analyze_results(s1_data, s2_data, STATIONS)


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-s", "-v", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
