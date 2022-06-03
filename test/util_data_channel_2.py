#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

import json
import sys
import time
from pprint import pformat

import structlog

sys.path.insert(0, "..")
sys.path.insert(0, "../tnc")
import data_handler
import helpers
import modem
import sock
import static

FIRST_RX = True


def t_setup(
    mycall: str,
    dxcall: str,
    lowbwmode: bool,
    t_transmit,
    t_process_data,
):
    # Disable data_handler testmode - This is required to test a conversation.
    data_handler.TESTMODE = False
    modem.RXCHANNEL = "/tmp/hfchannel2"
    modem.TESTMODE = True
    modem.TXCHANNEL = "/tmp/hfchannel1"
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
    tnc.log = structlog.get_logger("station2_DATA")
    # Limit the frame-ack timeout
    tnc.time_list_low_bw = [1, 1, 1]
    tnc.time_list_high_bw = [1, 1, 1]
    tnc.time_list = [1, 1, 1]

    # Create the modem
    t_modem = modem.RF()
    orig_tx_func = modem.RF.transmit
    modem.RF.transmit = t_transmit
    t_modem.log = structlog.get_logger("station2_RF")

    return tnc, orig_rx_func, orig_tx_func


def t_highsnr_arq_short_station2(
    parent_pipe,
    freedv_mode: str,
    n_frames_per_burst: int,
    mycall: str,
    dxcall: str,
    message: str,
    lowbwmode: bool,
):
    log = structlog.get_logger("station2")
    orig_tx_func: object
    orig_rx_func: object

    def t_transmit(self, mode, repeats: int, repeat_delay: int, frames: bytearray):
        """'Wrap' RF.transmit function to extract the arguments."""
        nonlocal orig_tx_func, parent_pipe

        t_frames = frames
        parent_pipe.send(t_frames)
        # log.info("S2 TX: ", frames=t_frames)
        for item in t_frames:
            frametype = int.from_bytes(item[:1], "big")
            log.info("S2 TX: ", TX=frametype)

        # Apologies for the Python "magic." "orig_func" is a pointer to the
        # original function captured before this one was put in place.
        orig_tx_func(self, mode, repeats, repeat_delay, frames)  # type: ignore

    def t_process_data(self, bytes_out, freedv, bytes_per_frame: int):
        """'Wrap' DATA.process_data function to extract the arguments."""
        nonlocal orig_rx_func, parent_pipe
        # global FIRST_RX
        # if FIRST_RX:
        #     FIRST_RX = False
        #     # Swallow the first frame
        #     orig_rx_func(self, bytes_out, freedv, bytes_per_frame)  # type: ignore

        t_bytes_out = bytes(bytes_out)
        parent_pipe.send(t_bytes_out)
        log.debug(
            "S2 RX: ",
            bytes_out=t_bytes_out,
            bytes_per_frame=bytes_per_frame,
        )
        frametype = int.from_bytes(t_bytes_out[:1], "big")
        log.info("S2 RX: ", RX=frametype)

        # Apologies for the Python "magic." "orig_func" is a pointer to the
        # original function captured before this one was put in place.
        orig_rx_func(self, bytes_out, freedv, bytes_per_frame)  # type: ignore

    tnc, orig_rx_func, orig_tx_func = t_setup(
        mycall, dxcall, lowbwmode, t_transmit, t_process_data
    )

    # data = {"type": "set", "command": "send_test_frame"}
    # sock.process_tnc_commands(json.dumps(data, indent=None))
    # time.sleep(0.5)
    # time.sleep(2)

    # This transaction should take less than 14 sec.
    timeout = time.time() + 20
    while "ARQ;RECEIVING;SUCCESS" not in static.INFO or static.ARQ_STATE:
        if time.time() > timeout:
            log.warning("station2 TIMEOUT", first=True)
            break
        time.sleep(0.5)
    log.info("station2, first", arq_state=pformat(static.ARQ_STATE))

    # Allow enough time for this side to receive the disconnect frame.
    timeout = time.time() + 10
    while "ARQ;SESSION;CLOSE" not in static.INFO:
        if time.time() > timeout:
            log.error("station2", TIMEOUT=True)
            break
        time.sleep(0.5)
    log.info("station2", arq_state=pformat(static.ARQ_STATE))

    # data = {"type": "arq", "command": "disconnect", "dxcallsign": dxcall}
    # sock.process_tnc_commands(json.dumps(data, indent=None))

    log.info("S2 DQT: ", DQ_Tx=pformat(tnc.data_queue_transmit.queue))
    log.info("S2 DQR: ", DQ_Rx=pformat(tnc.data_queue_received.queue))
    log.info("S2 Info: ", info=static.INFO)
    assert "DATACHANNEL;RECEIVEDOPENER" in static.INFO
    # assert "QRV;SENDING" in static.INFO
    # assert "ARQ;SESSION;CLOSE" in static.INFO
    assert "ARQ;RECEIVING;SUCCESS" in static.INFO
    log.error("station2: Exiting!")
