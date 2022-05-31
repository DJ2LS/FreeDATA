#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

import array
import base64
import json
import sys
import time
from pprint import pformat

import structlog

sys.path.insert(0, "..")
sys.path.insert(0, "../tnc")
import codec2
import data_handler
import helpers
import modem
import sock
import static


def t_highsnr_arq_short_station1(
    parent_pipe,
    freedv_mode: str,
    n_frames_per_burst: int,
    mycall: str,
    dxcall: str,
    message: str,
    lowbwmode: bool,
):
    log = structlog.get_logger("station1")
    orig_tx_func: object
    orig_rx_func: object

    def t_transmit(self, mode, repeats: int, repeat_delay: int, frames: bytearray):
        """'Wrap' RF.transmit function to extract the arguments."""
        nonlocal orig_tx_func, parent_pipe

        t_frames = frames
        parent_pipe.send(t_frames)
        # log.info("S1 TX: ", frames=t_frames)
        for item in t_frames:
            frametype = int.from_bytes(item[:1], "big")
            log.info("S1 TX: ", frametype=static.FRAME_TYPE(frametype).name)

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
        log.info("S1 RX: ", frametype=static.FRAME_TYPE(frametype).name)

        # Apologies for the Python "magic." "orig_func" is a pointer to the
        # original function captured before this one was put in place.
        orig_rx_func(self, bytes_out, freedv, bytes_per_frame)  # type: ignore

    # enable testmode
    data_handler.TESTMODE = True
    modem.RXCHANNEL = "/tmp/hfchannel1"
    modem.TESTMODE = True
    modem.TXCHANNEL = "/tmp/hfchannel2"
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

    # Create the modem
    t_modem = modem.RF()
    orig_tx_func = modem.RF.transmit
    modem.RF.transmit = t_transmit
    t_modem.log = structlog.get_logger("station1_RF")

    time.sleep(0.5)

    # Construct message to dxstation.
    # data = {"type": "ping", "command": "ping", "dxcallsign": dxcall}
    # data = {"type": "", "command": "cqcqcq", "dxcallsign": ""}
    # sock.process_tnc_commands(ujson.dumps(data))
    b64_str = str(base64.encodebytes(bytes(message, "UTF-8")), "UTF-8").strip()
    data = {
        "type": "arq",
        "command": "send_raw",
        "parameter": [
            {
                "data": b64_str,
                "dxcallsign": dxcall,
                "mode": codec2.FREEDV_MODE[freedv_mode].value,
                "n_frames": 1,
            }
        ],
    }

    sock.process_tnc_commands(json.dumps(data))
    time.sleep(0.5)

    # sock.process_tnc_commands(json.dumps(data))
    # time.sleep(0.5)

    # sock.process_tnc_commands(json.dumps(data))
    timeout = time.time() + 45
    while "ARQ;TRANSMITTING;SUCCESS" not in static.INFO:
        if time.time() > timeout:
            log.warning("station1", first=True)
            break
        time.sleep(0.1)

    # Construct disconnect message to dxstation.
    # data = {"type": "ping", "command": "ping", "dxcallsign": dxcall}

    # data = {"type": "arq", "command": "disconnect", "dxcallsign": dxcall}
    # sock.process_tnc_commands(json.dumps(data))
    # time.sleep(0.5)

    # sock.process_tnc_commands(json.dumps(data))
    # time.sleep(0.5)

    # sock.process_tnc_commands(json.dumps(data))
    # time.sleep(1)
    # sock.process_tnc_commands(json.dumps(data))
    # time.sleep(0.5)

    timeout = time.time() + 40
    while static.ARQ_STATE and tnc.data_queue_transmit.queue:
        if time.time() > timeout:
            log.error("station1", TIMEOUT=True)
            break
        time.sleep(0.5)
    log.info("station1", arq_state=pformat(static.ARQ_STATE))

    log.info("S1 DQT: ", info=pformat(tnc.data_queue_transmit.queue))
    log.info("S1 DQR: ", info=pformat(tnc.data_queue_received.queue))
    log.info("S1 Info: ", info=static.INFO)
    assert "DATACHANNEL;OPENING" in static.INFO
    assert "DATACHANNEL;OPEN" in static.INFO
    assert "ARQ;TRANSMITTING;SUCCESS" in static.INFO
    log.error("station1: Exiting!")
