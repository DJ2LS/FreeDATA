#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

import signal
import sys
import time
from typing import Callable

import structlog

sys.path.insert(0, "../tnc")
import data_handler
import helpers
import modem
import sock
import static

IRS_original_arq_cleanup: Callable
MESSAGE: str

log = structlog.get_logger("util_tnc_IRS")


def irs_arq_cleanup():
    """Replacement for modem.arq_cleanup to detect when to exit process."""
    log.info(
        "irs_arq_cleanup", socket_queue=sock.SOCKET_QUEUE.queue, message=MESSAGE.lower()
    )
    if '"arq":"transmission","status":"stopped"' in str(sock.SOCKET_QUEUE.queue):
        # log.info("irs_arq_cleanup", socket_queue=sock.SOCKET_QUEUE.queue)
        time.sleep(2)
        if f'"{MESSAGE.lower()}":"receiving"' not in str(
            sock.SOCKET_QUEUE.queue
        ) and f'"{MESSAGE.lower()}":"received"' not in str(sock.SOCKET_QUEUE.queue):
            print(f"{MESSAGE} was not received.")
            log.info("irs_arq_cleanup", socket_queue=sock.SOCKET_QUEUE.queue)
            # sys.exit does not terminate threads, and os_exit doesn't allow coverage collection.
            signal.raise_signal(signal.SIGKILL)

        signal.raise_signal(signal.SIGTERM)
    IRS_original_arq_cleanup()


def t_arq_irs(*args):
    # pylint: disable=global-statement
    global IRS_original_arq_cleanup, MESSAGE

    MESSAGE = args[0]
    tmp_path = args[1]

    sock.log = structlog.get_logger("util_tnc_IRS_sock")

    # enable testmode
    data_handler.TESTMODE = True
    modem.RXCHANNEL = tmp_path / "hfchannel2"
    modem.TESTMODE = True
    modem.TXCHANNEL = tmp_path / "hfchannel1"
    static.HAMLIB_RADIOCONTROL = "disabled"
    static.RESPOND_TO_CQ = True
    log.info("t_arq_irs:", RXCHANNEL=modem.RXCHANNEL)
    log.info("t_arq_irs:", TXCHANNEL=modem.TXCHANNEL)

    mycallsign = bytes("DN2LS-2", "utf-8")
    mycallsign = helpers.callsign_to_bytes(mycallsign)
    static.MYCALLSIGN = helpers.bytes_to_callsign(mycallsign)
    static.MYCALLSIGN_CRC = helpers.get_crc_24(static.MYCALLSIGN)
    static.MYGRID = bytes("AA12aa", "utf-8")
    static.SSID_LIST = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    # start data handler
    tnc = data_handler.DATA()
    tnc.log = structlog.get_logger("util_tnc_IRS_DATA")

    # Inject a way to exit the TNC infinite loop
    IRS_original_arq_cleanup = tnc.arq_cleanup
    tnc.arq_cleanup = irs_arq_cleanup

    # start modem
    t_modem = modem.RF()
    t_modem.log = structlog.get_logger("util_tnc_IRS_RF")

    # Set timeout
    timeout = time.time() + 15

    while time.time() < timeout:
        time.sleep(0.1)

    log.warning("queue:", queue=sock.SOCKET_QUEUE.queue)

    assert not "TIMEOUT!"


if __name__ == "__main__":
    print("This cannot be run as an application.")
    sys.exit(1)
