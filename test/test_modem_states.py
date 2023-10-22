#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test control frame messages over a high quality simulated audio channel.

Near end-to-end test for sending / receiving select control frames through the
Modem and modem and back through on the other station. Data injection initiates from the
queue used by the daemon process into and out of the Modem.

Can be invoked from CMake, pytest, coverage or directly.

Uses util_datac13.py in separate process to perform the data transfer.

@author: N2KIQ
"""

import multiprocessing
import numpy as np
import sys
import time

import pytest

# pylint: disable=wrong-import-position
sys.path.insert(0, "..")
sys.path.insert(0, "../modem")
import data_handler
import helpers
from global_instances import ARQ, AudioParam, Beacon, Channel, Daemon, HamlibParam, ModemParam, Station, Statistics, TCIParam, Modem


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

    # frame = bytearray(14)
    # frame[:1] = bytes([frame_type])
    # frame[1:4] = dxcallsign_crc
    # frame[4:7] = mycallsign_crc
    # frame[7:13] = mycallsign_bytes
    session_id = np.random.bytes(1)
    frame = bytearray(14)
    frame[:1] = bytes([frame_type])
    frame[1:2] = session_id
    frame[2:5] = dxcallsign_crc
    frame[5:8] = mycallsign_crc
    frame[8:14] = mycallsign_bytes

    return frame


def t_create_session_close_old(mycall: str, dxcall: str) -> bytearray:
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


def t_create_session_close(session_id: bytes, dxcall: str) -> bytearray:
    """
    Generate the session_close frame.

    :param session_id: Session to close
    :type mycall: int
    :return: Bytearray of the requested frame
    :rtype: bytearray
    """
    
    dxcallsign_bytes = helpers.callsign_to_bytes(dxcall)
    dxcallsign = helpers.bytes_to_callsign(dxcallsign_bytes)
    dxcallsign_crc = helpers.get_crc_24(dxcallsign)
    
    # return t_create_frame(223, mycall, dxcall)
    frame = bytearray(14)
    frame[:1] = bytes([223])
    frame[1:2] = session_id
    frame[2:5] = dxcallsign_crc

    return frame


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
    Station.ssid_list = [0, 1, 2, 3, 4]

    # Setup the static parameters for the connection.
    mycallsign_bytes = helpers.callsign_to_bytes(mycall)
    mycallsign = helpers.bytes_to_callsign(mycallsign_bytes)
    Station.mycallsign = mycallsign
    Station.mycallsign_crc = helpers.get_crc_24(mycallsign)

    dxcallsign_bytes = helpers.callsign_to_bytes(dxcall)
    dxcallsign = helpers.bytes_to_callsign(dxcallsign_bytes)
    Station.dxcallsign = dxcallsign
    Station.dxcallsign_crc = helpers.get_crc_24(dxcallsign)

    # Create the Modem
    modem = data_handler.DATA()
    modem.arq_cleanup()

    # Replace the heartbeat transmit routine with a No-Op.
    modem.transmit_session_heartbeat = t_tsh_dummy

    # Create frame to be 'received' by this station.
    create_frame = t_create_start_session(mycall=dxcall, dxcall=mycall)
    print_frame(create_frame)
    modem.received_session_opener(create_frame)

    assert helpers.callsign_to_bytes(Station.mycallsign) == mycallsign_bytes
    assert helpers.callsign_to_bytes(Station.dxcallsign) == dxcallsign_bytes

    assert ARQ.arq_session is True
    assert Modem.modem_state == "BUSY"
    assert ARQ.arq_session_state == "connecting"

    # Set up a frame from a non-associated station.
    # foreigncall_bytes = helpers.callsign_to_bytes("ZZ0ZZ-0")
    # foreigncall = helpers.bytes_to_callsign(foreigncall_bytes)

    # close_frame = t_create_session_close_old("ZZ0ZZ-0", "ZZ0ZZ-0")
    open_session = create_frame[1:2]
    wrong_session = np.random.bytes(1)
    while wrong_session == open_session:
        wrong_session = np.random.bytes(1)
    close_frame = t_create_session_close(wrong_session, dxcall)
    print_frame(close_frame)

    # assert (
    #     helpers.check_callsign(Station.dxcallsign, bytes(close_frame[4:7]))[0] is False
    # ), f"{helpers.get_crc_24(Station.dxcallsign)} == {bytes(close_frame[4:7])} but should be not equal."

    # assert (
    #     helpers.check_callsign(foreigncall, bytes(close_frame[4:7]))[0] is True
    # ), f"{helpers.get_crc_24(foreigncall)} != {bytes(close_frame[4:7])} but should be equal."

    # Send the non-associated session close frame to the Modem
    modem.received_session_close(close_frame)

    assert helpers.callsign_to_bytes(Station.mycallsign) == helpers.callsign_to_bytes(
        mycall
    ), f"{Station.mycallsign} != {mycall} but should equal."
    assert helpers.callsign_to_bytes(Station.dxcallsign) == helpers.callsign_to_bytes(
        dxcall
    ), f"{Station.dxcallsign} != {dxcall} but should equal."

    assert ARQ.arq_session is True
    assert Modem.modem_state == "BUSY"
    assert ARQ.arq_session_state == "connecting"


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
    Station.ssid_list = [0, 1, 2, 3, 4]

    # Setup the static parameters for the connection.
    mycallsign_bytes = helpers.callsign_to_bytes(mycall)
    mycallsign = helpers.bytes_to_callsign(mycallsign_bytes)
    Station.mycallsign = mycallsign
    Station.mycallsign_crc = helpers.get_crc_24(mycallsign)

    dxcallsign_bytes = helpers.callsign_to_bytes(dxcall)
    dxcallsign = helpers.bytes_to_callsign(dxcallsign_bytes)
    Station.dxcallsign = dxcallsign
    Station.dxcallsign_crc = helpers.get_crc_24(dxcallsign)

    # Create the Modem
    modem = data_handler.DATA()
    modem.arq_cleanup()

    # Replace the heartbeat transmit routine with our own, a No-Op.
    modem.transmit_session_heartbeat = t_tsh_dummy

    # Create packet to be 'received' by this station.
    create_frame = t_create_start_session(mycall=dxcall, dxcall=mycall)
    print_frame(create_frame)
    modem.received_session_opener(create_frame)
    print(ARQ.arq_session)
    assert ARQ.arq_session is True
    assert Modem.modem_state == "BUSY"
    assert ARQ.arq_session_state == "connecting"

    # Create packet to be 'received' by this station.
    # close_frame = t_create_session_close_old(mycall=dxcall, dxcall=mycall)
    open_session = create_frame[1:2]
    print(dxcall)
    print("#####################################################")
    close_frame = t_create_session_close(open_session, mycall)
    print(close_frame[2:5])
    print_frame(close_frame)
    modem.received_session_close(close_frame)

    assert helpers.callsign_to_bytes(Station.mycallsign) == mycallsign_bytes
    assert helpers.callsign_to_bytes(Station.dxcallsign) == dxcallsign_bytes

    assert ARQ.arq_session is False
    assert Modem.modem_state == "IDLE"
    assert ARQ.arq_session_state == "disconnected"


# These tests are pushed into separate processes as a workaround. These tests
# change the state of one of the static parts of the system. Unfortunately the
# specific state(s) maintained across tests in the same interpreter are not yet known.
# The other tests affected are: `test_modem.py` and the ARQ tests.


@pytest.mark.parametrize("mycall", ["AA1AA-2", "DE2DE-0", "E4AWQ-4"])
@pytest.mark.parametrize("dxcall", ["AA9AA-1", "DE2ED-0", "F6QWE-3"])
# @pytest.mark.flaky(reruns=2)
def test_foreign_disconnect(mycall: str, dxcall: str):
    proc = multiprocessing.Process(target=t_foreign_disconnect, args=(mycall, dxcall))
    # print("Starting threads.")
    proc.start()

    time.sleep(5.05)

    # print("Terminating threads.")
    proc.terminate()
    proc.join()

    # print(f"\nproc.exitcode={proc.exitcode}")
    assert proc.exitcode == 0


@pytest.mark.parametrize("mycall", ["AA1AA-2", "DE2DE-0", "M4AWQ-4"])
@pytest.mark.parametrize("dxcall", ["AA9AA-1", "DE2ED-0", "F6QWE-3"])
@pytest.mark.flaky(reruns=2)
def test_valid_disconnect(mycall: str, dxcall: str):
    proc = multiprocessing.Process(target=t_valid_disconnect, args=(mycall, dxcall))
    # print("Starting threads.")
    proc.start()

    time.sleep(5.05)

    # print("Terminating threads.")
    proc.terminate()
    proc.join()

    # print(f"\nproc.exitcode={proc.exitcode}")
    assert proc.exitcode == 0


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-v", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
