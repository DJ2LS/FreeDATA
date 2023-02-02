# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 21:25:14 2020

@author: DJ2LS
"""
import time
from datetime import datetime,timezone
import crcengine
import static
import structlog
import numpy as np
import threading

log = structlog.get_logger("helpers")


def wait(seconds: float) -> bool:
    """

    Args:
        seconds:

    Returns:
    """
    timeout = time.time() + seconds

    while time.time() < timeout:
        threading.Event().wait(0.01)
    return True


def get_crc_8(data) -> bytes:
    """Author: DJ2LS

    Get the CRC8 of a byte string

    param: data = bytes()

    Args:
        data:

    Returns:
        CRC-8 (CCITT) of the provided data as bytes
    """
    crc_algorithm = crcengine.new("crc8-ccitt")  # load crc8 library
    crc_data = crc_algorithm(data)
    crc_data = crc_data.to_bytes(1, byteorder="big")
    return crc_data


def get_crc_16(data) -> bytes:
    """Author: DJ2LS

    Get the CRC16 of a byte string

    param: data = bytes()

    Args:
        data:

    Returns:
        CRC-16 (CCITT) of the provided data as bytes
    """
    crc_algorithm = crcengine.new("crc16-ccitt-false")  # load crc16 library
    crc_data = crc_algorithm(data)
    crc_data = crc_data.to_bytes(2, byteorder="big")
    return crc_data


def get_crc_24(data) -> bytes:
    """Author: DJ2LS

    Get the CRC24-OPENPGP of a byte string
    https://github.com/GardenTools/CrcEngine#examples

    param: data = bytes()

    Args:
        data:

    Returns:
        CRC-24 (OpenPGP) of the provided data as bytes
    """
    crc_algorithm = crcengine.create(
        0x864CFB,
        24,
        0xB704CE,
        ref_in=False,
        ref_out=False,
        xor_out=0,
        name="crc-24-openpgp",
    )
    crc_data = crc_algorithm(data)
    crc_data = crc_data.to_bytes(3, byteorder="big")
    return crc_data


def get_crc_32(data: bytes) -> bytes:
    """Author: DJ2LS

    Get the CRC32 of a byte string

    param: data = bytes()

    Args:
      data:

    Returns:
        CRC-32 of the provided data as bytes
    """
    crc_algorithm = crcengine.new("crc32")  # load crc32 library
    crc_data = crc_algorithm(data)
    crc_data = crc_data.to_bytes(4, byteorder="big")
    return crc_data


def add_to_heard_stations(dxcallsign, dxgrid, datatype, snr, offset, frequency):
    """

    Args:
        dxcallsign:
        dxgrid:
        datatype:
        snr:
        offset:
        frequency:

    Returns:
        Nothing
    """
    # check if buffer empty
    if len(static.HEARD_STATIONS) == 0:
        static.HEARD_STATIONS.append(
            [dxcallsign, dxgrid, int(datetime.now(timezone.utc).timestamp()), datatype, snr, offset, frequency]
        )
    # if not, we search and update
    else:
        for i in range(len(static.HEARD_STATIONS)):
            # Update callsign with new timestamp
            if static.HEARD_STATIONS[i].count(dxcallsign) > 0:
                static.HEARD_STATIONS[i] = [
                    dxcallsign,
                    dxgrid,
                    int(time.time()),
                    datatype,
                    snr,
                    offset,
                    frequency,
                ]
                break
            # Insert if nothing found
            if i == len(static.HEARD_STATIONS) - 1:
                static.HEARD_STATIONS.append(
                    [
                        dxcallsign,
                        dxgrid,
                        int(time.time()),
                        datatype,
                        snr,
                        offset,
                        frequency,
                    ]
                )
                break


#    for idx, item in enumerate(static.HEARD_STATIONS):
#        if dxcallsign in item:
#            item = [dxcallsign, int(time.time())]
#            static.HEARD_STATIONS[idx] = item


def callsign_to_bytes(callsign) -> bytes:
    """

    Args:
        callsign:

    Returns:

    """
    # http://www.aprs.org/aprs11/SSIDs.txt
    # -0 Your primary station usually fixed and message capable
    # -1 generic additional station, digi, mobile, wx, etc
    # -2 generic additional station, digi, mobile, wx, etc
    # -3 generic additional station, digi, mobile, wx, etc
    # -4 generic additional station, digi, mobile, wx, etc
    # -5 Other networks (Dstar, Iphones, Androids, Blackberry's etc)
    # -6 Special activity, Satellite ops, camping or 6 meters, etc
    # -7 walkie talkies, HT's or other human portable
    # -8 boats, sailboats, RV's or second main mobile
    # -9 Primary Mobile (usually message capable)
    # -10 internet, Igates, echolink, winlink, AVRS, APRN, etc
    # -11 balloons, aircraft, spacecraft, etc
    # -12 APRStt, DTMF, RFID, devices, one-way trackers*, etc
    # -13 Weather stations
    # -14 Truckers or generally full time drivers
    # -15 generic additional station, digi, mobile, wx, etc

    # Try converting to bytestring if possible type string
    try:
        callsign = bytes(callsign, "utf-8")
    except TypeError:
        # This is expected depending on the type of the `callsign` argument.
        # log.debug("[HLP] callsign_to_bytes: Error converting callsign to bytes:", e=err)
        pass
    except Exception as err:
        log.debug("[HLP] callsign_to_bytes: Error callsign SSID to integer:", e=err)

    # Need this step to reduce the needed payload by the callsign
    # (stripping "-" out of the callsign)
    callsign = callsign.split(b"-")
    ssid = 0
    try:
        ssid = int(callsign[1])
    except IndexError:
        # This is expected when callsign doesn't have a dash.
        # log.debug("[HLP] callsign_to_bytes: Error callsign SSID to integer:", e=err)
        pass
    except Exception as err:
        log.debug("[HLP] callsign_to_bytes: Error callsign SSID to integer:", e=err)

    # callsign = callsign[0]
    # bytestring = bytearray(8)
    # bytestring[:len(callsign)] = callsign
    # bytestring[7:8] = bytes([ssid])

    # ---- callsign with encoding always 6 bytes long
    callsign = callsign[0].decode("utf-8")
    ssid = bytes([ssid]).decode("utf-8")
    return encode_call(callsign + ssid)
    # return bytes(bytestring)


def bytes_to_callsign(bytestring: bytes) -> bytes:
    """
    Convert our callsign, received by a frame to a callsign in a human readable format

    Args:
        bytestring:

    Returns:
        bytes
    """
    # http://www.aprs.org/aprs11/SSIDs.txt
    # -0 Your primary station usually fixed and message capable
    # -1 generic additional station, digi, mobile, wx, etc
    # -2 generic additional station, digi, mobile, wx, etc
    # -3 generic additional station, digi, mobile, wx, etc
    # -4 generic additional station, digi, mobile, wx, etc
    # -5 Other networks (Dstar, Iphones, Androids, Blackberry's etc)
    # -6 Special activity, Satellite ops, camping or 6 meters, etc
    # -7 walkie talkies, HT's or other human portable
    # -8 boats, sailboats, RV's or second main mobile
    # -9 Primary Mobile (usually message capable)
    # -10 internet, Igates, echolink, winlink, AVRS, APRN, etc
    # -11 balloons, aircraft, spacecraft, etc
    # -12 APRStt, DTMF, RFID, devices, one-way trackers*, etc
    # -13 Weather stations
    # -14 Truckers or generally full time drivers
    # -15 generic additional station, digi, mobile, wx, etc

    # we need to do this step to reduce the needed paypload by the callsign ( stripping "-" out of the callsign )
    """
    callsign = bytes(bytestring[:7])
    callsign = callsign.rstrip(b"\x00")
    ssid = int.from_bytes(bytes(bytestring[7:8]), "big")

    callsign = callsign + b"-"
    callsign = callsign.decode("utf-8")
    callsign = callsign + str(ssid)
    callsign = callsign.encode("utf-8")

    return bytes(callsign)
    """
    decoded = decode_call(bytestring)
    callsign = decoded[:-1]
    ssid = ord(bytes(decoded[-1], "utf-8"))
    return bytes(f"{callsign}-{ssid}", "utf-8")


def check_callsign(callsign: bytes, crc_to_check: bytes):
    """
    Function to check a crc against a callsign to calculate the
    ssid by generating crc until we find the correct SSID

    Args:
        callsign: Callsign which we want to check
        crc_to_check: The CRC which we want the callsign to check against

    Returns:
        [True, Callsign + SSID]
        False
    """

    log.debug("[HLP] check_callsign: Checking:", callsign=callsign)
    try:
        # We want the callsign without SSID
        callsign = callsign.split(b"-")[0]

    except IndexError:
        # This is expected when `callsign` doesn't have a dash.
        pass
    except Exception as err:
        log.debug("[HLP] check_callsign: Error callsign SSID to integer:", e=err)

    for ssid in static.SSID_LIST:
        call_with_ssid = bytearray(callsign)
        call_with_ssid.extend("-".encode("utf-8"))
        call_with_ssid.extend(str(ssid).encode("utf-8"))

        callsign_crc = get_crc_24(call_with_ssid)

        if callsign_crc == crc_to_check:
            log.debug("[HLP] check_callsign matched:", call_with_ssid=call_with_ssid)
            return [True, bytes(call_with_ssid)]

    return [False, b'']


def check_session_id(id: bytes, id_to_check: bytes):
    """
    Funktion to check if we received the correct session id

    Args:
        id: our own session id
        id_to_check: The session id byte we want to check

    Returns:
        True
        False
    """
    if id_to_check == b'\x00':
        return False
    log.debug("[HLP] check_sessionid: Checking:", ownid=id, check=id_to_check)
    return id == id_to_check


def encode_grid(grid):
    """
    @author: DB1UJ
    Args:
        grid:string: maidenhead QTH locater [a-r][a-r][0-9][0-9][a-x][a-x]
    Returns:
        4 bytes contains 26 bit valid data with encoded grid locator
    """
    out_code_word = 0

    grid = grid.upper()  # upper case to be save

    int_first = ord(grid[0]) - 65  # -65 offset for "A" become zero, utf8 table
    int_sec = ord(grid[1]) - 65  # -65 offset for "A" become zero, utf8 table

    int_val = (int_first * 18) + int_sec  # encode for modulo devision, 2 numbers in 1

    out_code_word = int_val & 0b111111111  # only 9 bit LSB A - R * A - R is needed
    out_code_word <<= 9  # shift 9 bit left having space next bits, letter A-R * A-R

    int_val = int(grid[2:4])  # number string to number int, highest value 99
    out_code_word |= int_val & 0b1111111  # using bit OR to add new value
    out_code_word <<= 7  # shift 7 bit left having space next bits, letter A-X

    int_val = ord(grid[4]) - 65  # -65 offset for 'A' become zero, utf8 table
    out_code_word |= int_val & 0b11111  # using bit OR to add new value
    out_code_word <<= 5  # shift 5 bit left having space next bits, letter A-X

    int_val = ord(grid[5]) - 65  # -65 offset for 'A' become zero, utf8 table
    out_code_word |= int_val & 0b11111  # using bit OR to add new value

    return out_code_word.to_bytes(length=4, byteorder="big")


def decode_grid(b_code_word: bytes):
    """
    @author: DB1UJ
    Args:
        b_code_word:bytes: 4 bytes with 26 bit valid data LSB
    Returns:
        grid:str: upper case maidenhead QTH locater [A-R][A-R][0-9][0-9][A-X][A-X]
    """
    code_word = int.from_bytes(b_code_word, byteorder="big", signed=False)

    grid = chr((code_word & 0b11111) + 65)
    code_word >>= 5

    grid = chr((code_word & 0b11111) + 65) + grid
    code_word >>= 7

    grid = str(int(code_word & 0b1111111)) + grid
    if (code_word & 0b1111111) < 10:
        grid = f"0{grid}"
    code_word >>= 9

    int_val = int(code_word & 0b111111111)
    int_first, int_sec = divmod(int_val, 18)
    return chr(int(int_first) + 65) + chr(int(int_sec) + 65) + grid


def encode_call(call):
    """
    @author: DB1UJ
    Args:
        call:string: ham radio call sign [A-Z,0-9], last char SSID 0-63

    Returns:
        6 bytes contains 6 bits/sign encoded 8 char call sign with binary SSID
        (only upper letters + numbers, SSID)
    """
    out_code_word = 0

    call = call.upper()  # upper case to be save

    for char in call:
        int_val = ord(char) - 48  # -48 reduce bits, begin with first number utf8 table
        out_code_word <<= 6  # shift left 6 bit, making space for a new char
        out_code_word |= (
            int_val & 0b111111
        )  # bit OR adds the new char, masked with AND 0b111111
    out_code_word >>= 6  # clean last char
    out_code_word <<= 6  # make clean space
    out_code_word |= ord(call[-1]) & 0b111111  # add the SSID uncoded only 0 - 63

    return out_code_word.to_bytes(length=6, byteorder="big")


def decode_call(b_code_word: bytes):
    """
    @author: DB1UJ
    Args:
        b_code_word:bytes: 6 bytes with 6 bits/sign valid data char signs LSB

    Returns:
        call:str: upper case ham radio call sign [A-Z,0-9] + binary SSID
    """
    code_word = int.from_bytes(b_code_word, byteorder="big", signed=False)
    ssid = chr(code_word & 0b111111)  # save the uncoded binary SSID

    call = str()
    while code_word != 0:
        call = chr((code_word & 0b111111) + 48) + call
        code_word >>= 6

    call = call[:-1] + ssid  # remove the last char from call and replace with SSID

    return call


def snr_to_bytes(snr):
    """create a byte from snr value """
    # make sure we have onl 1 byte snr
    # min max = -12.7 / 12.7
    # enough for detecting if a channel is good or bad
    snr = snr * 10
    snr = np.clip(snr, -127, 127)
    snr = int(snr).to_bytes(1, byteorder='big', signed=True)
    return snr


def snr_from_bytes(snr):
    """create int from snr byte"""
    snr = int.from_bytes(snr, byteorder='big', signed=True)
    snr = snr / 10
    return snr


def safe_execute(default, exception, function, *args):
    """
    https://stackoverflow.com/a/36671208
    from json import loads
    safe_execute("Oh no, explosions occurred!", TypeError, loads, None)

    """
    try:
        return function(*args)
    except exception:
        return default


def return_key_from_object(default, obj, key):
    try:
        return obj[key]
    except KeyError:
        return default