#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test control frame messages over a high quality simulated audio channel.

Near end-to-end test for sending / receiving select control frames through the
TNC and modem and back through on the other station. Data injection initiates from the
queue used by the daemon process into and out of the TNC.

Can be invoked from CMake, pytest, coverage or directly.

Uses util_datac0.py in separate process to perform the data transfer.
"""

import multiprocessing
import sys
import time

import pytest

# pylint: disable=wrong-import-position
sys.path.insert(0, "..")
sys.path.insert(0, "../tnc")
import data_handler
import helpers
import static


def print_frame(data: bytearray):
    """
    Pretty-print the provided frame.

    :param data: Frame to be output
    :type data: bytearray
    """
    print(f"Type   : {int(data[0])}")
    print(f"DXCRC  : {bytes(data[1:4])}")
    print(f"CallCRC: {bytes(data[4:7])}")
    print(f"Call   : {helpers.bytes_to_callsign(data[7:13])}")


def t_create_frame(frame_type: int, mycall: str, dxcall: str) -> bytearray:
    """
    Generate the requested frame.

    :param frame_type: The numerical type of the desired frame.
    :type frame_type: int
    :param mycall: Callsign of the near station
    :type mycall: str
    :param dxcall: Callsign of the far station
    :type dxcall: str
    :return: Bytearray of the requested frame
    :rtype: bytearray
    """
    mycallsign_bytes = helpers.callsign_to_bytes(mycall)
    mycallsign = helpers.bytes_to_callsign(mycallsign_bytes)
    mycallsign_crc = helpers.get_crc_24(mycallsign)

    dxcallsign_bytes = helpers.callsign_to_bytes(dxcall)
    dxcallsign = helpers.bytes_to_callsign(dxcallsign_bytes)
    dxcallsign_crc = helpers.get_crc_24(dxcallsign)

    frame = bytearray(14)
    frame[:1] = bytes([frame_type])
    frame[1:4] = dxcallsign_crc
    frame[4:7] = mycallsign_crc
    frame[7:13] = mycallsign_bytes

    return frame


def t_create_session_close(mycall: str, dxcall: str) -> bytearray:
    """
    Generate the session_close frame.

    :param mycall: Callsign of the near station
    :type mycall: str
    :param dxcall: Callsign of the far station
    :type dxcall: str
    :return: Bytearray of the requested frame
    :rtype: bytearray
    """
    return t_create_frame(223, mycall, dxcall)


def t_create_start_session(mycall: str, dxcall: str) -> bytearray:
    """
    Generate the create_session frame.

    :param mycall: Callsign of the near station
    :type mycall: str
    :param dxcall: Callsign of the far station
    :type dxcall: str
    :return: Bytearray of the requested frame
    :rtype: bytearray
    """
    return t_create_frame(221, mycall, dxcall)


def t_tsh_dummy():
    """Replacement function for transmit_session_heartbeat"""
    print("In transmit_session_heartbeat")


def t_foreign_disconnect(mycall: str, dxcall: str):
    """
    Execute test to validate that receiving a session open frame sets the correct machine
    state.

    :param mycall: Callsign of the near station
    :type mycall: str
    :param dxcall: Callsign of the far station
    :type dxcall: str
    :return: Bytearray of the requested frame
    :rtype: bytearray
    """
    # Set the SSIDs we'll use for this test.
    static.SSID_LIST = [0, 1, 2, 3, 4]

    # Setup the static parameters for the connection.
    mycallsign_bytes = helpers.callsign_to_bytes(mycall)
    mycallsign = helpers.bytes_to_callsign(mycallsign_bytes)
    static.MYCALLSIGN = mycallsign
    static.MYCALLSIGN_CRC = helpers.get_crc_24(mycallsign)

    dxcallsign_bytes = helpers.callsign_to_bytes(dxcall)
    dxcallsign = helpers.bytes_to_callsign(dxcallsign_bytes)
    static.DXCALLSIGN = dxcallsign
    static.DXCALLSIGN_CRC = helpers.get_crc_24(dxcallsign)

    # Create the TNC
    tnc = data_handler.DATA()
    tnc.arq_cleanup()

    # Replace the heartbeat transmit routine with a No-Op.
    tnc.transmit_session_heartbeat = t_tsh_dummy

    # Create frame to be 'received' by this station.
    create_frame = t_create_start_session(mycall=dxcall, dxcall=mycall)
    print_frame(create_frame)
    tnc.received_session_opener(create_frame)

    assert helpers.callsign_to_bytes(static.MYCALLSIGN) == mycallsign_bytes
    assert helpers.callsign_to_bytes(static.DXCALLSIGN) == dxcallsign_bytes

    assert static.ARQ_SESSION is True
    assert static.TNC_STATE == "BUSY"
    assert static.ARQ_SESSION_STATE == "connecting"

    # Set up a frame from a non-associated station.
    foreigncall_bytes = helpers.callsign_to_bytes("ZZ0ZZ-0")
    foreigncall = helpers.bytes_to_callsign(foreigncall_bytes)

    close_frame = t_create_session_close("ZZ0ZZ-0", "ZZ0ZZ-0")
    print_frame(close_frame)
    assert (
        helpers.check_callsign(static.DXCALLSIGN, bytes(close_frame[4:7]))[0] is False
    ), f"{helpers.get_crc_24(static.DXCALLSIGN)} == {bytes(close_frame[4:7])} but should be not equal."

    assert (
        helpers.check_callsign(foreigncall, bytes(close_frame[4:7]))[0] is True
    ), f"{helpers.get_crc_24(foreigncall)} != {bytes(close_frame[4:7])} but should be equal."

    # Send the non-associated session close frame to the TNC
    tnc.received_session_close(close_frame)

    assert helpers.callsign_to_bytes(static.MYCALLSIGN) == helpers.callsign_to_bytes(
        mycall
    ), f"{static.MYCALLSIGN} != {mycall} but should equal."
    assert helpers.callsign_to_bytes(static.DXCALLSIGN) == helpers.callsign_to_bytes(
        dxcall
    ), f"{static.DXCALLSIGN} != {dxcall} but should equal."

    assert static.ARQ_SESSION is True
    assert static.TNC_STATE == "BUSY"
    assert static.ARQ_SESSION_STATE == "connecting"


def t_valid_disconnect(mycall: str, dxcall: str):
    """
    Execute test to validate that receiving a session open frame sets the correct machine
    state.

    :param mycall: Callsign of the near station
    :type mycall: str
    :param dxcall: Callsign of the far station
    :type dxcall: str
    :return: Bytearray of the requested frame
    :rtype: bytearray
    """
    # Set the SSIDs we'll use for this test.
    static.SSID_LIST = [0, 1, 2, 3, 4]

    # Setup the static parameters for the connection.
    mycallsign_bytes = helpers.callsign_to_bytes(mycall)
    mycallsign = helpers.bytes_to_callsign(mycallsign_bytes)
    static.MYCALLSIGN = mycallsign
    static.MYCALLSIGN_CRC = helpers.get_crc_24(mycallsign)

    dxcallsign_bytes = helpers.callsign_to_bytes(dxcall)
    dxcallsign = helpers.bytes_to_callsign(dxcallsign_bytes)
    static.DXCALLSIGN = dxcallsign
    static.DXCALLSIGN_CRC = helpers.get_crc_24(dxcallsign)

    # Create the TNC
    tnc = data_handler.DATA()
    tnc.arq_cleanup()

    # Replace the heartbeat transmit routine with our own, a No-Op.
    tnc.transmit_session_heartbeat = t_tsh_dummy

    # Create packet to be 'received' by this station.
    create_frame = t_create_start_session(mycall=dxcall, dxcall=mycall)
    print_frame(create_frame)
    tnc.received_session_opener(create_frame)

    assert static.ARQ_SESSION is True
    assert static.TNC_STATE == "BUSY"
    assert static.ARQ_SESSION_STATE == "connecting"

    # Create packet to be 'received' by this station.
    close_frame = t_create_session_close(mycall=dxcall, dxcall=mycall)
    print_frame(close_frame)
    tnc.received_session_close(close_frame)

    assert helpers.callsign_to_bytes(static.MYCALLSIGN) == mycallsign_bytes
    assert helpers.callsign_to_bytes(static.DXCALLSIGN) == dxcallsign_bytes

    assert static.ARQ_SESSION is False
    assert static.TNC_STATE == "IDLE"
    assert static.ARQ_SESSION_STATE == "disconnected"


# These tests are pushed into separate processes as a workaround. These tests
# change the state of one of the static parts of the system. Unfortunately the
# specific state(s) maintained across tests in the same interpreter are not yet known.
# The other tests affected are: `test_tnc.py` and the ARQ tests.


@pytest.mark.parametrize("mycall", ["AA1AA-2", "DE2DE-0", "E4AWQ-4"])
@pytest.mark.parametrize("dxcall", ["AA9AA-1", "DE2ED-0", "F6QWE-3"])
@pytest.mark.flaky(reruns=2)
def test_foreign_disconnect(mycall: str, dxcall: str):
    proc = multiprocessing.Process(target=t_foreign_disconnect, args=(mycall, dxcall))
    # print("Starting threads.")
    proc.start()

    time.sleep(0.05)

    # print("Terminating threads.")
    proc.terminate()
    proc.join()

    # print(f"\n{proc.exitcode=}")
    assert proc.exitcode == 0


@pytest.mark.parametrize("mycall", ["AA1AA-2", "DE2DE-0", "M4AWQ-4"])
@pytest.mark.parametrize("dxcall", ["AA9AA-1", "DE2ED-0", "F6QWE-3"])
@pytest.mark.flaky(reruns=2)
def test_valid_disconnect(mycall: str, dxcall: str):
    proc = multiprocessing.Process(target=t_valid_disconnect, args=(mycall, dxcall))
    # print("Starting threads.")
    proc.start()

    time.sleep(0.05)

    # print("Terminating threads.")
    proc.terminate()
    proc.join()

    # print(f"\n{proc.exitcode=}")
    assert proc.exitcode == 0


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-v", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
