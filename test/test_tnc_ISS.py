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

ISS_original_arq_cleanup = object
MESSAGE: str


def iss_arq_cleanup():
    """Replacement for modem.arq_cleanup to detect when to exit process."""
    if "TRANSMISSION;STOPPED" in static.INFO:
        print(f"{static.INFO=}")
        time.sleep(1)
        # sys.exit does not terminate threads.
        # pylint: disable=protected-access
        if f"{MESSAGE};SENDING" not in static.INFO:
            print(f"{MESSAGE} was not sent.")
            os._exit(1)

        os._exit(0)
    ISS_original_arq_cleanup()


def test_arq_iss(*args):
    # pylint: disable=global-statement
    global ISS_original_arq_cleanup, MESSAGE

    MESSAGE = args[0]

    # enable testmode
    data_handler.TESTMODE = True
    modem.TESTMODE = True
    modem.RXCHANNEL = "/tmp/hfchannel1"
    modem.TXCHANNEL = "/tmp/hfchannel2"
    static.HAMLIB_RADIOCONTROL = "disabled"

    mycallsign = bytes("DJ2LS-2", "utf-8")
    mycallsign = helpers.callsign_to_bytes(mycallsign)
    static.MYCALLSIGN = helpers.bytes_to_callsign(mycallsign)
    static.MYCALLSIGN_CRC = helpers.get_crc_24(static.MYCALLSIGN)
    static.MYGRID = bytes("AA12aa", "utf-8")
    static.SSID_LIST = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    dxcallsign = b"DN2LS-0"
    dxcallsign = helpers.callsign_to_bytes(dxcallsign)
    dxcallsign = helpers.bytes_to_callsign(dxcallsign)
    static.DXCALLSIGN = dxcallsign
    static.DXCALLSIGN_CRC = helpers.get_crc_24(static.DXCALLSIGN)

    bytes_out = b'{"dt":"f","fn":"zeit.txt","ft":"text\\/plain","d":"data:text\\/plain;base64,MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=","crc":"123123123"}'

    # start data handler
    tnc = data_handler.DATA()

    # Inject a way to exit the TNC infinite loop
    ISS_original_arq_cleanup = tnc.arq_cleanup
    tnc.arq_cleanup = iss_arq_cleanup

    # start modem
    t_modem = modem.RF()

    # mode = codec2.freedv_get_mode_value_by_name(FREEDV_MODE)
    # n_frames_per_burst = N_FRAMES_PER_BURST

    # add command to data qeue
    """
    elif data[0] == 'ARQ_RAW':
        # [0] ARQ_RAW
        # [1] DATA_OUT bytes
        # [2] MODE int
        # [3] N_FRAMES_PER_BURST int
        # [4] self.transmission_uuid str
        # [5] mycallsign with ssid
    """
    # data_handler.DATA_QUEUE_TRANSMIT.put(['ARQ_RAW', bytes_out, 255, n_frames_per_burst, '123', b'DJ2LS-0'])

    # for _ in range(4):
    if MESSAGE in ["BEACON"]:
        data_handler.DATA_QUEUE_TRANSMIT.put([MESSAGE, 5, True])
    elif MESSAGE in ["PING", "CONNECT"]:
        data_handler.DATA_QUEUE_TRANSMIT.put([MESSAGE, dxcallsign])
    else:
        data_handler.DATA_QUEUE_TRANSMIT.put([MESSAGE])

    time.sleep(1.5)

    # for i in range(4):
    #    data_handler.DATA_QUEUE_TRANSMIT.put(['PING', b'DN2LS-2'])

    data_handler.DATA_QUEUE_TRANSMIT.put(["STOP"])

    # Set timeout
    timeout = time.time() + 10

    while time.time() < timeout:
        time.sleep(0.1)

    assert not "TIMEOUT!"


if __name__ == "__main__":
    print("This cannot be run as an application.")
    sys.exit(-1)
