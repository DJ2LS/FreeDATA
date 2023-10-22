# -*- coding: utf-8 -*-
"""
Receive-side station emulator for connect frame tests over a high quality simulated audio channel.

Near end-to-end test for sending / receiving connection control frames through the
Modem and modem and back through on the other station. Data injection initiates from the
queue used by the daemon process into and out of the Modem.

Invoked from test_chat_text.py.

@author: N2KIQ
"""

import time
from pprint import pformat
from typing import Callable

import data_handler
import helpers
import modem
import sock
from static import ARQ, AudioParam, Beacon, Channel, Daemon, HamlibParam, ModemParam, Station, Statistics, TCIParam, Modem
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
    modem.RXCHANNEL = tmp_path / "hfchannel2"
    modem.TESTMODE = True
    modem.TXCHANNEL = tmp_path / "hfchannel1"
    HamlibParam.hamlib_radiocontrol = "disabled"
    Modem.low_bandwidth_mode = lowbwmode
    Station.mygrid = bytes("AA12aa", "utf-8")
    Modem.respond_to_cq = True
    Station.ssid_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    # override ARQ SESSION STATE for allowing disconnect command
    ARQ.arq_session_state = "connected"

    mycallsign = helpers.callsign_to_bytes(mycall)
    mycallsign = helpers.bytes_to_callsign(mycallsign)
    Station.mycallsign = mycallsign
    Station.mycallsign_crc = helpers.get_crc_24(Station.mycallsign)

    dxcallsign = helpers.callsign_to_bytes(dxcall)
    dxcallsign = helpers.bytes_to_callsign(dxcallsign)
    Station.dxcallsign = dxcallsign
    Station.dxcallsign_crc = helpers.get_crc_24(Station.dxcallsign)

    # Create the Modem
    modem = data_handler.DATA()
    orig_rx_func = data_handler.DATA.process_data
    data_handler.DATA.process_data = t_process_data
    modem.log = structlog.get_logger("station2_DATA")
    # Limit the frame-ack timeout
    modem.time_list_low_bw = [1, 1, 1]
    modem.time_list_high_bw = [1, 1, 1]
    modem.time_list = [1, 1, 1]
    # Limit number of retries
    modem.rx_n_max_retries_per_burst = 5

    # Create the modem
    t_modem = modem.RF()
    orig_tx_func = modem.RF.transmit
    modem.RF.transmit = t_transmit
    t_modem.log = structlog.get_logger("station2_RF")

    return modem, orig_rx_func, orig_tx_func


def t_highsnr_arq_short_station2(
    parent_pipe,
    freedv_mode: str,
    n_frames_per_burst: int,
    mycall: str,
    dxcall: str,
    message: str,
    lowbwmode: bool,
    tmp_path,
):
    log = structlog.get_logger("station2")
    orig_tx_func: Callable
    orig_rx_func: Callable
    log.info("t_highsnr_arq_short_station2:", TMP_PATH=tmp_path)

    def t_transmit(self, mode, repeats: int, repeat_delay: int, frames: bytearray):
        """'Wrap' RF.transmit function to extract the arguments."""
        nonlocal orig_tx_func, parent_pipe

        t_frames = frames
        parent_pipe.send(t_frames)
        # log.info("S2 TX: ", frames=t_frames)
        for item in t_frames:
            frametype = int.from_bytes(item[:1], "big")  # type: ignore
            log.info("S2 TX: ", TX=frametype)

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
        log.info("S2 RX: ", RX=frametype)

        # Apologies for the Python "magic." "orig_func" is a pointer to the
        # original function captured before this one was put in place.
        orig_rx_func(self, bytes_out, freedv, bytes_per_frame)  # type: ignore

    modem, orig_rx_func, orig_tx_func = t_setup(
        mycall, dxcall, lowbwmode, t_transmit, t_process_data, tmp_path
    )

    log.info("t_highsnr_arq_short_station2:", RXCHANNEL=modem.RXCHANNEL)
    log.info("t_highsnr_arq_short_station2:", TXCHANNEL=modem.TXCHANNEL)

    # Assure the test completes.
    timeout = time.time() + 25
    # Compare with the string conversion instead of repeatedly dumping
    # the queue to an object for comparisons.
    while (
        '"arq":"transmission","status":"received"' not in str(sock.SOCKET_QUEUE.queue)
        or ARQ.arq_state
    ):
        if time.time() > timeout:
            log.warning("station2 TIMEOUT", first=True)
            break
        time.sleep(0.5)
    log.info("station2, first", arq_state=pformat(ARQ.arq_state))

    # Allow enough time for this side to receive the disconnect frame.
    timeout = time.time() + 20
    while '"arq":"session","status":"close"' not in str(sock.SOCKET_QUEUE.queue):
        if time.time() > timeout:
            log.warning("station2", TIMEOUT=True)
            break
        time.sleep(0.5)
    log.info("station2", arq_state=pformat(ARQ.arq_state))

    # log.info("S2 DQT: ", DQ_Tx=pformat(modem.data_queue_transmit.queue))
    # log.info("S2 DQR: ", DQ_Rx=pformat(modem.data_queue_received.queue))
    log.info("S2 Socket: ", socket_queue=pformat(sock.SOCKET_QUEUE.queue))

    assert '"arq":"transmission","status":"received"' in str(sock.SOCKET_QUEUE.queue)

    assert '"arq":"session","status":"close"' in str(sock.SOCKET_QUEUE.queue)
    log.warning("station2: Exiting!")
