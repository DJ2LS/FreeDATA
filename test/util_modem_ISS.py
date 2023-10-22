# -*- coding: utf-8 -*-
"""
Send-side station emulator for connect frame tests over a high quality simulated audio channel.

Near end-to-end test for sending / receiving connection control frames through the
TNC and modem and back through on the other station. Data injection initiates from the
queue used by the daemon process into and out of the TNC.

Invoked from test_modem.py.

@author: DJ2LS, N2KIQ
"""

import json
import signal
import sys
import time
from typing import Callable

import structlog

sys.path.insert(0, "../modem")
import data_handler
import helpers
import modem
import sock
import static
from global_instances import ARQ, AudioParam, Beacon, Channel, Daemon, HamlibParam, ModemParam, Station, Statistics, TCIParam, Modem

ISS_original_arq_cleanup: Callable
MESSAGE: str

log = structlog.get_logger("util_modem_ISS")


def iss_arq_cleanup():
    """Replacement for modem.arq_cleanup to detect when to exit process."""
    log.info(
        "iss_arq_cleanup", socket_queue=sock.SOCKET_QUEUE.queue, message=MESSAGE.lower()
    )
    if '"arq":"transmission","status":"stopped"' in str(sock.SOCKET_QUEUE.queue):
        # log.info("iss_arq_cleanup", socket_queue=sock.SOCKET_QUEUE.queue)
        time.sleep(1)
        if f'"{MESSAGE.lower()}":"transmitting"' not in str(
            sock.SOCKET_QUEUE.queue
        ) and f'"{MESSAGE.lower()}":"sending"' not in str(sock.SOCKET_QUEUE.queue):
            print(f"{MESSAGE} was not sent.")
            log.info("iss_arq_cleanup", socket_queue=sock.SOCKET_QUEUE.queue)
            # sys.exit does not terminate threads, and os_exit doesn't allow coverage collection.
            signal.raise_signal(signal.SIGKILL)

        signal.raise_signal(signal.SIGTERM)
    ISS_original_arq_cleanup()


def t_arq_iss(*args):
    # not sure why importing at top level isn't working
    import modem
    import data_handler
    # pylint: disable=global-statement
    global ISS_original_arq_cleanup, MESSAGE

    MESSAGE = args[0]
    tmp_path = args[1]

    sock.log = structlog.get_logger("util_modem_ISS_sock")

    # enable testmode
    data_handler.TESTMODE = True
    modem.RXCHANNEL = tmp_path / "hfchannel1"
    modem.TESTMODE = True
    modem.TXCHANNEL = tmp_path / "hfchannel2"
    HamlibParam.hamlib_radiocontrol = "disabled"
    log.info("t_arq_iss:", RXCHANNEL=modem.RXCHANNEL)
    log.info("t_arq_iss:", TXCHANNEL=modem.TXCHANNEL)

    mycallsign = bytes("DJ2LS-2", "utf-8")
    mycallsign = helpers.callsign_to_bytes(mycallsign)
    Station.mycallsign = helpers.bytes_to_callsign(mycallsign)
    Station.mycallsign_CRC = helpers.get_crc_24(Station.mycallsign)
    Station.mygrid = bytes("AA12aa", "utf-8")
    Station.ssid_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    dxcallsign = b"DN2LS-0"
    dxcallsign = helpers.callsign_to_bytes(dxcallsign)
    dxcallsign = helpers.bytes_to_callsign(dxcallsign)
    Station.dxcallsign = dxcallsign
    Station.dxcallsign_CRC = helpers.get_crc_24(Station.dxcallsign)

    bytes_out = b'{"dt":"f","fn":"zeit.txt","ft":"text\\/plain","d":"data:text\\/plain;base64,MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=","crc":"123123123"}'

    # start data handler
    data_handler = data_handler.DATA()
    data_handler.log = structlog.get_logger("util_modem_ISS_DATA")

    # Inject a way to exit the TNC infinite loop
    ISS_original_arq_cleanup = data_handler.arq_cleanup
    data_handler.arq_cleanup = iss_arq_cleanup

    # start modem
    t_modem = modem.RF()
    t_modem.log = structlog.get_logger("util_modem_ISS_RF")

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

    data = {}
    if MESSAGE in ["CONNECT"]:
        data = {
            "type": "arq",
            "command": "connect",
            "dxcallsign": str(dxcallsign, encoding="UTF-8"),
        }
    else:
        assert not MESSAGE, f"{MESSAGE} not known to test."

    time.sleep(2.5)

    sock.ThreadedTCPRequestHandler.process_modem_commands(None,json.dumps(data, indent=None))
    sock.ThreadedTCPRequestHandler.process_modem_commands(None,json.dumps(data, indent=None))
    sock.ThreadedTCPRequestHandler.process_modem_commands(None,json.dumps(data, indent=None))

    time.sleep(7.5)

    data = {"type": "arq", "command": "stop_transmission"}
    sock.ThreadedTCPRequestHandler.process_modem_commands(None,json.dumps(data, indent=None))

    time.sleep(2.5)
    sock.ThreadedTCPRequestHandler.process_modem_commands(None,json.dumps(data, indent=None))

    # Set timeout
    timeout = time.time() + 15

    while time.time() < timeout:
        time.sleep(0.1)

    log.warning("queue:", queue=sock.SOCKET_QUEUE.queue)

    assert not "TIMEOUT!"


if __name__ == "__main__":
    print("This cannot be run as an application.")
    sys.exit(-1)
