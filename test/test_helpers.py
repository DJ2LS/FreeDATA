#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test common helper routines used throughout the TNC.

Can be invoked from CMake, pytest, coverage or directly.

Uses no other files.

@author: N2KIQ
"""

import sys

import helpers
import pytest
from static import ARQ, AudioParam, Beacon, Channel, Daemon, HamlibParam, ModemParam, Station, Statistics, TCIParam, TNC


@pytest.mark.parametrize("callsign", ["AA1AA", "DE2DE", "E4AWQ-4"])
def test_check_callsign(callsign: str):
    """
    Execute test to demonstrate how to create and verify callsign checksums.
    """
    Station.ssid_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

    t_callsign_bytes = helpers.callsign_to_bytes(callsign)
    t_callsign = helpers.bytes_to_callsign(t_callsign_bytes)
    t_callsign_crc = helpers.get_crc_24(t_callsign)

    dxcallsign_bytes = helpers.callsign_to_bytes("ZZ9ZZA-0")
    dxcallsign = helpers.bytes_to_callsign(dxcallsign_bytes)
    dxcallsign_crc = helpers.get_crc_24(dxcallsign)

    assert helpers.check_callsign(t_callsign, t_callsign_crc)[0] is True
    assert helpers.check_callsign(t_callsign, dxcallsign_crc)[0] is False


@pytest.mark.parametrize("callsign", ["AA1AA-2", "DE2DE-0", "E4AWQ-4"])
def test_callsign_to_bytes(callsign: str):
    """
    Execute test to demonsrate symmetry when converting callsigns to and from byte arrays.
    """
    Station.ssid_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

    t_callsign_crc = helpers.get_crc_24(bytes(callsign, "UTF-8"))
    t_callsign_bytes = helpers.callsign_to_bytes(callsign)
    t_callsign = helpers.bytes_to_callsign(t_callsign_bytes)

    assert helpers.check_callsign(t_callsign, t_callsign_crc)[0] is True
    assert helpers.check_callsign(t_callsign, t_callsign_crc)[1] == bytes(
        callsign, "UTF-8"
    )


@pytest.mark.parametrize("callsign", ["AA1AA-2", "DE2DE-0", "e4awq-4"])
def test_encode_callsign(callsign: str):
    """
    Execute test to demonsrate symmetry when encoding and decoding callsigns.
    """
    callenc = helpers.encode_call(callsign)
    calldec = helpers.decode_call(callenc)

    assert callsign.upper() != calldec


@pytest.mark.parametrize("gridsq", ["EM98dc", "DE01GG", "EF42sW"])
def test_encode_grid(gridsq: str):
    """
    Execute test to demonsrate symmetry when encoding and decoding grid squares.
    """

    gridenc = helpers.encode_grid(gridsq)
    griddec = helpers.decode_grid(gridenc)

    assert gridsq.upper() == griddec


@pytest.mark.parametrize("gridsq", ["SM98dc", "DE01GZ", "EV42sY"])
@pytest.mark.xfail(reason="Invalid gridsquare provided")
def test_invalid_grid(gridsq: str):
    """
    Execute test to demonsrate symmetry when encoding and decoding grid squares.
    """

    gridenc = helpers.encode_grid(gridsq)
    griddec = helpers.decode_grid(gridenc)

    assert gridsq.upper() != griddec


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-v", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
