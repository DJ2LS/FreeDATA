"""
Tests for the FreeDATA modem.
"""

import multiprocessing
import sys
import time

import pytest

sys.path.insert(0, "..")
sys.path.insert(0, "../tnc")
import helpers
import modem
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
    """Replacement function for transmit"""
    print("In t_tsh_dummy")


def t_modem():
    """
    Execute test to validate that receiving a session open frame sets the correct machine
    state.
    """
    t_mode = t_repeats = t_repeat_delay = 0
    t_frames = []

    # enable testmode
    modem.TESTMODE = True
    modem.RXCHANNEL = "/tmp/hfchannel1"
    modem.TXCHANNEL = "/tmp/hfchannel2"
    static.HAMLIB_RADIOCONTROL = "disabled"

    def t_tx_dummy(mode, repeats, repeat_delay, frames):
        """Replacement function for transmit"""
        print(f"t_tx_dummy: In transmit({mode}, {repeats}, {repeat_delay}, {frames})")
        nonlocal t_mode, t_repeats, t_repeat_delay, t_frames
        t_mode = mode
        t_repeats = repeats
        t_repeat_delay = repeat_delay
        t_frames = frames[:]
        static.TRANSMITTING = False

    # Create the modem
    local_modem = modem.RF()

    # Replace transmit routine with our own, an effective No-Op.
    local_modem.transmit = t_tx_dummy

    txbuffer = t_create_start_session("AA9AA", "DC2EJ")

    # Start the transmission
    static.TRANSMITTING = True
    modem.MODEM_TRANSMIT_QUEUE.put([14, 5, 250, txbuffer])
    while static.TRANSMITTING:
        time.sleep(0.1)

    # Check that the contents were transferred correctly.
    assert t_mode == 14
    assert t_repeats == 5
    assert t_repeat_delay == 250
    assert t_frames == txbuffer


def test_modem_queue():
    proc = multiprocessing.Process(target=t_modem, args=())
    # print("Starting threads.")
    proc.start()

    time.sleep(0.5)

    # print("Terminating threads.")
    proc.terminate()
    proc.join()

    # print(f"\n{proc.exitcode=}")
    assert proc.exitcode == 0


if __name__ == "__main__":
    # Run pytest with the current script as the filename.
    ecode = pytest.main(["-v", "-s", sys.argv[0]])
    if ecode == 0:
        print("errors: 0")
    else:
        print(ecode)
