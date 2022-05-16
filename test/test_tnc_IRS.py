#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

import os
import sys
import time

sys.path.insert(0, "..")
sys.path.insert(0, "../tnc")
import data_handler
import helpers
import modem
import static

IRS_original_arq_cleanup = object
MESSAGE: str


def irs_arq_cleanup():
    """Replacement for modem.arq_cleanup to detect when to exit process."""
    if "TRANSMISSION;STOPPED" in static.INFO:
        print(f"{static.INFO=}")
        time.sleep(2)
        # sys.exit does not terminate threads.
        # pylint: disable=protected-access
        if f"{MESSAGE};RECEIVING" not in static.INFO:
            print(f"{MESSAGE} was not received.")
            os._exit(1)

        os._exit(0)
    IRS_original_arq_cleanup()


def t_arq_irs(*args):
    # pylint: disable=global-statement
    global IRS_original_arq_cleanup, MESSAGE

    MESSAGE = args[0]

    # enable testmode
    data_handler.TESTMODE = True
    modem.TESTMODE = True
    modem.RXCHANNEL = "/tmp/hfchannel2"
    modem.TXCHANNEL = "/tmp/hfchannel1"
    static.HAMLIB_RADIOCONTROL = "disabled"
    static.RESPOND_TO_CQ = True

    mycallsign = bytes("DN2LS-2", "utf-8")
    mycallsign = helpers.callsign_to_bytes(mycallsign)
    static.MYCALLSIGN = helpers.bytes_to_callsign(mycallsign)
    static.MYCALLSIGN_CRC = helpers.get_crc_24(static.MYCALLSIGN)
    static.MYGRID = bytes("AA12aa", "utf-8")
    static.SSID_LIST = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    # start data handler
    tnc = data_handler.DATA()

    # Inject a way to exit the TNC infinite loop
    IRS_original_arq_cleanup = tnc.arq_cleanup
    tnc.arq_cleanup = irs_arq_cleanup

    # start modem
    t_modem = modem.RF()

    # Set timeout
    timeout = time.time() + 10

    while time.time() < timeout:
        time.sleep(0.1)

    assert not "TIMEOUT!"


if __name__ == "__main__":
    print("This cannot be run as an application.")
    sys.exit(1)
