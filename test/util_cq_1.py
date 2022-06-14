#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

import json
import time
from pprint import pformat
from typing import Callable

import data_handler
import helpers
import modem
import sock
import static
import structlog


def t_setup(
    mycall: str,
    dxcall: str,
    lowbwmode: bool,
    t_transmit,
    t_process_data,
    tmp_path,
):
    # Disable data_handler testmode - This is required to test a conversation.
    data_handler.TESTMODE = False
    modem.RXCHANNEL = tmp_path / "hfchannel1"
    modem.TESTMODE = True
    modem.TXCHANNEL = tmp_path / "hfchannel2"
    static.HAMLIB_RADIOCONTROL = "disabled"
    static.LOW_BANDWIDTH_MODE = lowbwmode
    static.MYGRID = bytes("AA12aa", "utf-8")
    static.RESPOND_TO_CQ = True
    static.SSID_LIST = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    mycallsign = helpers.callsign_to_bytes(mycall)
    mycallsign = helpers.bytes_to_callsign(mycallsign)
    static.MYCALLSIGN = mycallsign
    static.MYCALLSIGN_CRC = helpers.get_crc_24(static.MYCALLSIGN)

    dxcallsign = helpers.callsign_to_bytes(dxcall)
    dxcallsign = helpers.bytes_to_callsign(dxcallsign)
    static.DXCALLSIGN = dxcallsign
    static.DXCALLSIGN_CRC = helpers.get_crc_24(static.DXCALLSIGN)

    # Create the TNC
    tnc = data_handler.DATA()
    orig_rx_func = data_handler.DATA.process_data
    data_handler.DATA.process_data = t_process_data
    tnc.log = structlog.get_logger("station1_DATA")
    # Limit the frame-ack timeout
    tnc.time_list_low_bw = [3, 1, 1]
    tnc.time_list_high_bw = [3, 1, 1]
    tnc.time_list = [3, 1, 1]
    # Limit number of retries
    tnc.rx_n_max_retries_per_burst = 4

    # Create the modem
    t_modem = modem.RF()
    orig_tx_func = modem.RF.transmit
    modem.RF.transmit = t_transmit
    t_modem.log = structlog.get_logger("station1_RF")

    return tnc, orig_rx_func, orig_tx_func


def t_cq1(
    parent_pipe,
    mycall: str,
    dxcall: str,
    lowbwmode: bool,
    tmp_path,
):
    log = structlog.get_logger("station1")
    orig_tx_func: Callable
    orig_rx_func: Callable
    log.info("t_cq1:", TMP_PATH=tmp_path)

    def t_transmit(self, mode, repeats: int, repeat_delay: int, frames: bytearray):
        """'Wrap' RF.transmit function to extract the arguments."""
        nonlocal orig_tx_func, parent_pipe

        t_frames = frames
        parent_pipe.send(t_frames)
        # log.info("S1 TX: ", frames=t_frames)
        for item in t_frames:
            frametype = int.from_bytes(item[:1], "big")  # type: ignore
            log.info("S1 TX: ", TX=frametype)

        # Apologies for the Python "magic." "orig_func" is a pointer to the
        # original function captured before this one was put in place.
        orig_tx_func(self, mode, repeats, repeat_delay, frames)  # type: ignore

    def t_process_data(self, bytes_out, freedv, bytes_per_frame: int):
        """'Wrap' DATA.process_data function to extract the arguments."""
        nonlocal orig_rx_func, parent_pipe

        t_bytes_out = bytes(bytes_out)
        parent_pipe.send(t_bytes_out)
        log.debug(
            "S1 RX: ",
            bytes_out=t_bytes_out,
            bytes_per_frame=bytes_per_frame,
        )
        frametype = int.from_bytes(t_bytes_out[:1], "big")
        log.info("S1 RX: ", RX=frametype)

        # Apologies for the Python "magic." "orig_func" is a pointer to the
        # original function captured before this one was put in place.
        orig_rx_func(self, bytes_out, freedv, bytes_per_frame)  # type: ignore

    tnc, orig_rx_func, orig_tx_func = t_setup(
        mycall, dxcall, lowbwmode, t_transmit, t_process_data, tmp_path
    )

    log.info("t_cq1:", RXCHANNEL=modem.RXCHANNEL)
    log.info("t_cq1:", TXCHANNEL=modem.TXCHANNEL)

    # Construct message to start cq.
    data = {"type": "command", "command": "cqcqcq"}

    sock.process_tnc_commands(json.dumps(data, indent=None))
    time.sleep(0.5)
    sock.process_tnc_commands(json.dumps(data, indent=None))

    timeout = time.time() + 5
    # Compare with the string conversion instead of repeatedly dumping
    # the queue to an object for comparisons.
    while '"cq":"transmitting"' not in str(sock.SOCKET_QUEUE.queue):
        if time.time() > timeout:
            log.warning("station1 TIMEOUT", first=True)
            break
        time.sleep(0.1)
    log.info("station1, first", arq_state=pformat(static.ARQ_STATE))

    data = {"type": "arq", "command": "disconnect", "dxcallsign": dxcall}
    sock.process_tnc_commands(json.dumps(data, indent=None))
    time.sleep(0.5)
    sock.process_tnc_commands(json.dumps(data, indent=None))

    # Allow enough time for this side to process the disconnect frame.
    timeout = time.time() + 5
    while static.ARQ_STATE or tnc.data_queue_transmit.queue:
        if time.time() > timeout:
            log.error("station1", TIMEOUT=True)
            break
        time.sleep(0.5)
    log.info("station1", arq_state=pformat(static.ARQ_STATE))

    # log.info("S1 DQT: ", DQ_Tx=pformat(tnc.data_queue_transmit.queue))
    # log.info("S1 DQR: ", DQ_Rx=pformat(tnc.data_queue_received.queue))
    # log.info("S1 Socket: ", socket_queue=pformat(sock.SOCKET_QUEUE.queue))
    assert '"cq":"transmitting"' in str(sock.SOCKET_QUEUE.queue)
    assert '"cq":"failed"' not in str(sock.SOCKET_QUEUE.queue)
    assert '"command_response":"disconnect","status":"OK"' in str(
        sock.SOCKET_QUEUE.queue
    )
    log.error("station1: Exiting!")
