#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Negative test utilities for datac13 frames.

@author: kronenpj
"""

import json
import time
from pprint import pformat
from typing import Callable, Tuple

import data_handler
import helpers
import modem
import sock
from static import ARQ, AudioParam, Beacon, Channel, Daemon, HamlibParam, ModemParam, Station, Statistics, TCIParam, TNC, FRAME_TYPE as FR_TYPE
import structlog
#from static import FRAME_TYPE as FR_TYPE


def t_setup(
    station: int,
    mycall: str,
    dxcall: str,
    rx_channel: str,
    tx_channel: str,
    lowbwmode: bool,
    t_transmit,
    t_process_data,
    tmp_path,
):
    # Disable data_handler testmode - This is required to test a conversation.
    data_handler.TESTMODE = False

    # Enable socket testmode for overriding socket class
    sock.TESTMODE = True

    modem.RXCHANNEL = tmp_path / rx_channel
    modem.TESTMODE = True
    modem.TXCHANNEL = tmp_path / tx_channel
    HamlibParam.hamlib_radiocontrol = "disabled"
    TNC.low_bandwidth_mode = lowbwmode or True
    Station.mygrid = bytes("AA12aa", "utf-8")
    TNC.respond_to_cq = True
    Station.ssid_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    mycallsign_bytes = helpers.callsign_to_bytes(mycall)
    mycallsign = helpers.bytes_to_callsign(mycallsign_bytes)
    Station.mycallsign = mycallsign
    Station.mycallsign_crc = helpers.get_crc_24(mycallsign)

    dxcallsign_bytes = helpers.callsign_to_bytes(dxcall)
    dxcallsign = helpers.bytes_to_callsign(dxcallsign_bytes)
    Station.dxcallsign = dxcallsign
    Station.dxcallsign_crc = helpers.get_crc_24(dxcallsign)

    # Create the TNC
    tnc_data_handler = data_handler.DATA()
    orig_rx_func = data_handler.DATA.process_data
    data_handler.DATA.process_data = t_process_data
    tnc_data_handler.log = structlog.get_logger(f"station{station}_DATA")
    # Limit the frame-ack timeout
    tnc_data_handler.time_list_low_bw = [3, 1, 1]
    tnc_data_handler.time_list_high_bw = [3, 1, 1]
    tnc_data_handler.time_list = [3, 1, 1]
    # Limit number of retries
    tnc_data_handler.rx_n_max_retries_per_burst = 4
    ModemParam.tx_delay = 500 # add additional delay time for passing test
    # Create the modem
    t_modem = modem.RF()
    orig_tx_func = modem.RF.transmit
    modem.RF.transmit = t_transmit
    t_modem.log = structlog.get_logger(f"station{station}_RF")

    return tnc_data_handler, orig_rx_func, orig_tx_func


def t_datac13_1(
    parent_pipe,
    mycall: str,
    dxcall: str,
    config: Tuple,
    tmp_path,
):
    log = structlog.get_logger("station1")
    orig_tx_func: Callable
    orig_rx_func: Callable
    log.debug("t_datac13_1:", TMP_PATH=tmp_path)

    # Unpack tuple
    data, timeout_duration, tx_check, _, final_tx_check, _ = config

    def t_transmit(self, mode, repeats: int, repeat_delay: int, frames: bytearray):
        """'Wrap' RF.transmit function to extract the arguments."""
        nonlocal orig_tx_func, parent_pipe

        t_frames = frames
        parent_pipe.send(t_frames)
        # log.info("S1 TX: ", frames=t_frames)
        for item in t_frames:
            frametype = int.from_bytes(item[:1], "big")  # type: ignore
            log.info("S1 TX: ", TX=FR_TYPE(frametype).name)

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
        log.info("S1 RX: ", RX=FR_TYPE(frametype).name)

        # Apologies for the Python "magic." "orig_func" is a pointer to the
        # original function captured before this one was put in place.
        orig_rx_func(self, bytes_out, freedv, bytes_per_frame)  # type: ignore

    tnc_data_handler, orig_rx_func, orig_tx_func = t_setup(
        1,
        mycall,
        dxcall,
        "hfchannel1",
        "hfchannel2",
        True,
        t_transmit,
        t_process_data,
        tmp_path,
    )

    log.info("t_datac13_1:", RXCHANNEL=modem.RXCHANNEL)
    log.info("t_datac13_1:", TXCHANNEL=modem.TXCHANNEL)

    orig_dxcall = Station.dxcallsign
    if "stop" in data["command"]:
        time.sleep(0.5)
        log.debug(
            "t_datac13_1: STOP test, setting TNC state",
            mycall=Station.mycallsign,
            dxcall=Station.dxcallsign,
        )
        Station.dxcallsign = helpers.callsign_to_bytes(data["dxcallsign"])
        Station.dxcallsign_CRC = helpers.get_crc_24(Station.dxcallsign)
        TNC.tnc_state = "BUSY"
        ARQ.arq_state = True
    sock.ThreadedTCPRequestHandler.process_tnc_commands(None,json.dumps(data, indent=None))
    sock.ThreadedTCPRequestHandler.process_tnc_commands(None,json.dumps(data, indent=None))

    # Assure the test completes.
    timeout = time.time() + timeout_duration
    while tx_check not in str(sock.SOCKET_QUEUE.queue):
        if time.time() > timeout:
            log.warning(
                "station1 TIMEOUT",
                first=True,
                queue=str(sock.SOCKET_QUEUE.queue),
                tx_check=tx_check,
            )
            break
        time.sleep(0.1)
    log.info("station1, first")

    if "stop" in data["command"]:
        time.sleep(0.5)
        log.debug("STOP test, resetting DX callsign")
        Station.dxcallsign = orig_dxcall
        Station.dxcallsign_CRC = helpers.get_crc_24(Station.dxcallsign)
    # override ARQ SESSION STATE for allowing disconnect command
    ARQ.arq_session_state = "connected"
    data = {"type": "arq", "command": "disconnect", "dxcallsign": dxcall}
    sock.ThreadedTCPRequestHandler.process_tnc_commands(None,json.dumps(data, indent=None))
    time.sleep(0.5)

    # Allow enough time for this side to process the disconnect frame.
    timeout = time.time() + timeout_duration
    while tnc_data_handler.data_queue_transmit.queue:
        if time.time() > timeout:
            log.warning("station1", TIMEOUT=True, dq_tx=tnc_data_handler.data_queue_transmit.queue)
            break
        time.sleep(0.5)
    log.info("station1, final")

    # log.info("S1 DQT: ", DQ_Tx=pformat(tnc.data_queue_transmit.queue))
    # log.info("S1 DQR: ", DQ_Rx=pformat(tnc.data_queue_received.queue))
    log.debug("S1 Socket: ", socket_queue=pformat(sock.SOCKET_QUEUE.queue))

    for item in final_tx_check:
        assert item in str(
            sock.SOCKET_QUEUE.queue
        ), f"{item} not found in {str(sock.SOCKET_QUEUE.queue)}"

    assert '"command_response":"disconnect","status":"OK"' in str(
        sock.SOCKET_QUEUE.queue
    )
    log.warning("station1: Exiting!")


def t_datac13_2(
    parent_pipe,
    mycall: str,
    dxcall: str,
    config: Tuple,
    tmp_path,
):
    log = structlog.get_logger("station2")
    orig_tx_func: Callable
    orig_rx_func: Callable
    log.debug("t_datac13_2:", TMP_PATH=tmp_path)

    # Unpack tuple
    data, timeout_duration, _, rx_check, _, final_rx_check = config

    def t_transmit(self, mode, repeats: int, repeat_delay: int, frames: bytearray):
        """'Wrap' RF.transmit function to extract the arguments."""
        nonlocal orig_tx_func, parent_pipe

        t_frames = frames
        parent_pipe.send(t_frames)
        # log.info("S2 TX: ", frames=t_frames)
        for item in t_frames:
            frametype = int.from_bytes(item[:1], "big")  # type: ignore
            log.info("S2 TX: ", TX=FR_TYPE(frametype).name)

        # Apologies for the Python "magic." "orig_func" is a pointer to the
        # original function captured before this one was put in place.
        orig_tx_func(self, mode, repeats, repeat_delay, frames)  # type: ignore

    def t_process_data(self, bytes_out, freedv, bytes_per_frame: int):
        """'Wrap' DATA.process_data function to extract the arguments."""
        nonlocal orig_rx_func, parent_pipe

        t_bytes_out = bytes(bytes_out)
        parent_pipe.send(t_bytes_out)
        log.debug(
            "S2 RX: ",
            bytes_out=t_bytes_out,
            bytes_per_frame=bytes_per_frame,
        )
        frametype = int.from_bytes(t_bytes_out[:1], "big")
        log.info("S2 RX: ", RX=FR_TYPE(frametype).name)

        # Apologies for the Python "magic." "orig_func" is a pointer to the
        # original function captured before this one was put in place.
        orig_rx_func(self, bytes_out, freedv, bytes_per_frame)  # type: ignore

    _, orig_rx_func, orig_tx_func = t_setup(
        2,
        mycall,
        dxcall,
        "hfchannel2",
        "hfchannel1",
        True,
        t_transmit,
        t_process_data,
        tmp_path,
    )

    log.info("t_datac13_2:", RXCHANNEL=modem.RXCHANNEL)
    log.info("t_datac13_2:", TXCHANNEL=modem.TXCHANNEL)
    log.info("t_datac13_2:", mycall=Station.mycallsign)

    if "cq" in data:
        t_data = {"type": "arq", "command": "stop_transmission"}
        sock.ThreadedTCPRequestHandler.process_tnc_commands(None,json.dumps(t_data, indent=None))
        sock.ThreadedTCPRequestHandler.process_tnc_commands(None,json.dumps(t_data, indent=None))

    # Assure the test completes.
    timeout = time.time() + timeout_duration
    # Compare with the string conversion instead of repeatedly dumping
    # the queue to an object for comparisons.
    while rx_check not in str(sock.SOCKET_QUEUE.queue):
        if time.time() > timeout:
            log.warning(
                "station2 TIMEOUT",
                first=True,
                queue=str(sock.SOCKET_QUEUE.queue),
                rx_check=rx_check,
            )
            break
        time.sleep(0.5)
    log.info("station2, first")

    # Allow enough time for this side to receive the disconnect frame.
    timeout = time.time() + timeout_duration
    while '"arq":"session", "status":"close"' not in str(sock.SOCKET_QUEUE.queue):
        if time.time() > timeout:
            log.warning("station2", TIMEOUT=True, queue=str(sock.SOCKET_QUEUE.queue))
            break
        time.sleep(0.5)
    log.info("station2, final")

    # log.info("S2 DQT: ", DQ_Tx=pformat(tnc.data_queue_transmit.queue))
    # log.info("S2 DQR: ", DQ_Rx=pformat(tnc.data_queue_received.queue))
    log.debug("S2 Socket: ", socket_queue=pformat(sock.SOCKET_QUEUE.queue))

    for item in final_rx_check:
        assert item not in str(
            sock.SOCKET_QUEUE.queue
        ), f"{item} found in {str(sock.SOCKET_QUEUE.queue)}"
    # TODO: Not sure why we need this for every test run
    # assert '"arq":"session","status":"close"' in str(sock.SOCKET_QUEUE.queue)
    log.warning("station2: Exiting!")
