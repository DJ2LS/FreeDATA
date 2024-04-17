# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 21:25:14 2020

@author: DJ2LS
"""
import time
from datetime import datetime,timezone
import crcengine
import structlog
import numpy as np
import threading
import hashlib
import hmac
import os
import sys
from pathlib import Path
import platform
import subprocess
import psutil
import glob


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


def get_crc_8(data: str) -> bytes:
    """Author: DJ2LS

    Get the CRC8 of a byte string

    param: data = bytes()

    Args:
        data:

    Returns:
        CRC-8 (CCITT) of the provided data as bytes
    """
    if not isinstance(data, (bytes)) or isinstance(data, (bytearray)):
        data = bytes(data,"utf-8")

    crc_algorithm = crcengine.new("crc8-ccitt")  # load crc8 library
    crc_data = crc_algorithm(data)
    crc_data = crc_data.to_bytes(1, byteorder="big")
    return crc_data


def get_crc_16(data: str) -> bytes:
    """Author: DJ2LS

    Get the CRC16 of a byte string

    param: data = bytes()

    Args:
        data:

    Returns:
        CRC-16 (CCITT) of the provided data as bytes
    """
    if not isinstance(data, (bytes)) or isinstance(data, (bytearray)):
        data = bytes(data,"utf-8")
    
    crc_algorithm = crcengine.new("crc16-ccitt-false")  # load crc16 library
    return crc_algorithm(data).to_bytes(2, byteorder="big")

def get_crc_24(data: str) -> bytes:
    """Author: DJ2LS

    Get the CRC24-OPENPGP of a byte string
    https://github.com/GardenTools/CrcEngine#examples

    param: data = bytes()

    Args:
        data:

    Returns:
        CRC-24 (OpenPGP) of the provided data as bytes
    """
    if not isinstance(data, (bytes)) or isinstance(data, (bytearray)):
        data = bytes(data,'utf-8')

    params = crcengine.CrcParams(0x864cfb, 24, 0xb704ce, reflect_in=False, reflect_out=False, xor_out=0)
    crc_algorithm = crcengine.create(params=params)
    return crc_algorithm(data).to_bytes(3,byteorder="big")


def get_crc_32(data: str) -> bytes:
    """Author: DJ2LS

    Get the CRC32 of a byte string

    param: data = bytes()

    Args:
      data:

    Returns:
        CRC-32 of the provided data as bytes
    """
    if not isinstance(data, (bytes)) or isinstance(data, (bytearray)):
        data = bytes(data, "utf-8")
    crc_algorithm = crcengine.new("crc32")  # load crc32 library
    return crc_algorithm(data).to_bytes(4, byteorder="big")


from datetime import datetime, timezone
import time


def add_to_heard_stations(dxcallsign, dxgrid, datatype, snr, offset, frequency, heard_stations_list, distance_km=None,
                          distance_miles=None, away_from_key=False):
    """
    Args:
        dxcallsign (str): The callsign of the DX station.
        dxgrid (str): The Maidenhead grid square of the DX station.
        datatype (str): The type of data received (e.g., FT8, CW).
        snr (int): Signal-to-noise ratio of the received signal.
        offset (float): Frequency offset.
        frequency (float): Base frequency of the received signal.
        heard_stations_list (list): List containing heard stations.
        distance_km (float): Distance to the DX station in kilometers.
        distance_miles (float): Distance to the DX station in miles.
        away_from_key (bool): Away from key indicator

    Returns:
        Nothing. The function updates the heard_stations_list in-place.
    """
    # Convert current timestamp to an integer
    current_timestamp = int(datetime.now(timezone.utc).timestamp())

    # Initialize the new entry
    new_entry = [
        dxcallsign, dxgrid, current_timestamp, datatype, snr, offset, frequency, distance_km, distance_miles, away_from_key
    ]

    # Check if the buffer is empty or if the callsign is not already in the list
    if not any(dxcallsign == station[0] for station in heard_stations_list):
        heard_stations_list.append(new_entry)
    else:
        # Search for the existing entry and update
        for i, entry in enumerate(heard_stations_list):
            if entry[0] == dxcallsign:
                heard_stations_list[i] = new_entry
                break


def callsign_to_bytes(callsign: str) -> bytes:
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
        callsign = callsign.encode("utf-8")
    except TypeError:
        # This is expected depending on the type of the `callsign` argument.
        # log.debug("[HLP] callsign_to_bytes: Error converting callsign to bytes:", e=err)
        pass
    except Exception as err:
        log.debug("[HLP] callsign_to_bytes: Error converting callsign to bytes:", e=err, data=callsign)

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
        log.debug("[HLP] callsign_to_bytes: Error splitting callsign/ssid:", e=err)

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


def check_callsign(callsign: str, crc_to_check: bytes, ssid_list):
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
    print(callsign)
    if not isinstance(callsign, (bytes)):
        callsign = bytes(callsign,'utf-8')

    try:
        # We want the callsign without SSID
        splitted_callsign = callsign.split(b"-")
        callsign = splitted_callsign[0]
        ssid = splitted_callsign[1].decode()

    except IndexError:
        # This is expected when `callsign` doesn't have a dash.
        ssid = 0
    except Exception as err:
        log.debug("[HLP] check_callsign: Error converting to bytes:", e=err)

    # ensure, we are always have the own ssid in ssid_list even if it is empty
    if ssid not in ssid_list:
        ssid_list.append(str(ssid))

    for ssid in ssid_list:
        call_with_ssid = callsign + b'-' + (str(ssid)).encode('utf-8')
        callsign_crc = get_crc_24(call_with_ssid)
        callsign_crc = callsign_crc.hex()

        if callsign_crc == crc_to_check:
            log.debug("[HLP] check_callsign matched:", call_with_ssid=call_with_ssid, checksum=crc_to_check)
            return [True, call_with_ssid.decode()]

    log.debug("[HLP] check_callsign: Checking:", callsign=callsign, crc_to_check=crc_to_check, own_crc=callsign_crc)
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


def bool_to_string(state):
    return "True" if state else "False"




def get_hmac_salt(dxcallsign: bytes, mycallsign: bytes):
    filename = f"freedata_hmac_STATION_{mycallsign.decode('utf-8')}_REMOTE_{dxcallsign.decode('utf-8')}.txt"
    if sys.platform in ["linux"]:

        if hasattr(sys, "_MEIPASS"):
            filepath = getattr(sys, "_MEIPASS") + '/hmac/' + filename
        else:
            subfolder = Path('hmac')
            filepath = subfolder / filename


    elif sys.platform in ["darwin"]:
        if hasattr(sys, "_MEIPASS"):
            filepath = getattr(sys, "_MEIPASS") + '/hmac/' + filename
        else:
            subfolder = Path('hmac')
            filepath = subfolder / filename

    elif sys.platform in ["win32", "win64"]:
        if hasattr(sys, "_MEIPASS"):
            filepath = getattr(sys, "_MEIPASS") + '/hmac/' + filename
        else:
            subfolder = Path('hmac')
            filepath = subfolder / filename
    else:
        try:
            subfolder = Path('hmac')
            filepath = subfolder / filename
        except Exception as e:
            log.error(
                "[Modem] [HMAC] File lookup error", file=filepath,
            )

    # check if file exists else return false
    if not check_if_file_exists(filepath):
        return False

    log.info("[SCK] [HMAC] File lookup", file=filepath)

    try:
        with open(filepath, "r") as file:
            line = file.readlines()
            hmac_salt = bytes(line[-1], "utf-8").split(b'\n')
            hmac_salt = hmac_salt[0]
            return hmac_salt if delete_last_line_from_hmac_list(filepath, -1) else False
    except Exception as e:
        log.warning("[SCK] [HMAC] File lookup failed", file=filepath, e=e)
        return False

def search_hmac_salt(dxcallsign: bytes, mycallsign: bytes, search_token, data_frame, token_iters):

    filename = f"freedata_hmac_STATION_{mycallsign.decode('utf-8')}_REMOTE_{dxcallsign.decode('utf-8')}.txt"
    if sys.platform in ["linux"]:

        if hasattr(sys, "_MEIPASS"):
            filepath = getattr(sys, "_MEIPASS") + '/hmac/' + filename
        else:
            subfolder = Path('hmac')
            filepath = subfolder / filename


    elif sys.platform in ["darwin"]:
        if hasattr(sys, "_MEIPASS"):
            filepath = getattr(sys, "_MEIPASS") + '/hmac/' + filename
        else:
            subfolder = Path('hmac')
            filepath = subfolder / filename

    elif sys.platform in ["win32", "win64"]:
        if hasattr(sys, "_MEIPASS"):
            filepath = getattr(sys, "_MEIPASS") + '/hmac/' + filename
        else:
            subfolder = Path('hmac')
            filepath = subfolder / filename
    else:
        try:
            subfolder = Path('hmac')
            filepath = subfolder / filename
        except Exception as e:
            log.error(
                "[Modem] [HMAC] File lookup error", file=filepath,
            )

    # check if file exists else return false
    if not check_if_file_exists(filepath):
        log.warning(
            "[Modem] [HMAC] Token file not found", file=filepath,
        )
        return False

    try:
        with open(filepath, "r") as file:
            token_list = file.readlines()

            token_iters = min(token_iters, len(token_list))
            for _ in range(1, token_iters + 1):
                key = token_list[len(token_list) - _][:-1]
                key = bytes(key, "utf-8")
                search_digest = hmac.new(key, data_frame, hashlib.sha256).digest()[:4]
                # TODO Remove this debugging information if not needed anymore
                # print("-----------------------------------------")
                # print(_)
                # print(f" key-------------{key}")
                # print(f" key-------------{token_list[len(token_list) - _][:-1]}")
                # print(f" key-------------{key.hex()}")
                # print(f" search token----{search_token.hex()}")
                # print(f" search digest---{search_digest.hex()}")
                if search_token.hex() == search_digest.hex():
                    token_position = len(token_list) - _
                    delete_last_line_from_hmac_list(filepath, token_position)
                    log.info(
                        "[Modem] [HMAC] Signature found", expected=search_token.hex(),
                    )
                    return True


        log.warning(
            "[Modem] [HMAC] Signature not found", expected=search_token.hex(), filepath=filepath,
        )
        return False

    except Exception as e:
        log.warning(
            "[Modem] [HMAC] Lookup failed", e=e, expected=search_token,
        )
        return False


def delete_last_line_from_hmac_list(filepath, position):
    # check if file exists else return false
    if not check_if_file_exists(filepath):
        return False

    try:
        linearray = []
        with open(filepath, "r") as file:
            linearray = file.readlines()[:position]
            #print(linearray)

        with open(filepath, "w") as file:
            #print(linearray)
            for line in linearray:
                file.write(line)

        return True

    except Exception:
        return False

def check_if_file_exists(path):
    try:
        # check if file size is present and filesize > 0
        if os.path.isfile(path):
            filesize = os.path.getsize(path)
            if filesize > 0:
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        log.warning(
            "[Modem] [FILE] Lookup failed", e=e, path=path,
        )
        return False


def set_bit(byte, position, value):
    """Set the bit at 'position' to 'value' in the given byte."""
    if not 0 <= position <= 7:
        raise ValueError("Position must be between 0 and 7")

    if value:
        return byte | (1 << position)
    else:
        return byte & ~(1 << position)

def get_bit(byte, position):
    """Get the boolean value of the bit at 'position' in the given byte."""
    if not 0 <= position <= 7:
        raise ValueError("Position must be between 0 and 7")

    return (byte & (1 << position)) != 0

def set_flag(byte, flag_name, value, flag_dict):
    """Set the flag in the byte according to the flag dictionary.

    # Define a dictionary mapping flag names to their bit positions
        flag_dict = {
            'FLAG1': 0,  # Bit position for FLAG1
            'FLAG2': 1,  # Bit position for FLAG2, etc.
            'FLAG3': 2
        }

    """
    if flag_name not in flag_dict:
        raise ValueError(f"Unknown flag name: {flag_name}")
    position = flag_dict[flag_name]
    return set_bit(byte, position, value)


def get_flag(byte, flag_name, flag_dict):
    """Get the value of the flag from the byte according to the flag dictionary."""
    if flag_name not in flag_dict:
        raise ValueError(f"Unknown flag name: {flag_name}")
    position = flag_dict[flag_name]
    return get_bit(byte, position)


def find_binary_paths(binary_name="rigctld", search_system_wide=False):
    """
    Search for a binary within the current working directory, its subdirectories, and optionally,
    system-wide locations and the PATH environment variable.

    :param binary_name: The base name of the binary to search for, without extension.
    :param search_system_wide: Boolean flag to enable or disable system-wide search.
    :return: A list of full paths to the binary if found, otherwise an empty list.
    """
    binary_paths = []  # Initialize an empty list to store found paths
    # Adjust binary name for Windows
    if platform.system() == 'Windows':
        binary_name += ".exe"

    # Search in the current working directory and subdirectories
    root_path = os.getcwd()
    for dirpath, dirnames, filenames in os.walk(root_path):
        if binary_name in filenames:
            binary_paths.append(os.path.join(dirpath, binary_name))

    # If system-wide search is enabled, look in system locations and PATH
    if search_system_wide:
        system_paths = os.environ.get('PATH', '').split(os.pathsep)
        # Optionally add common binary locations for Unix-like and Windows systems
        if platform.system() != 'Windows':
            system_paths.extend(['/usr/bin', '/usr/local/bin', '/bin'])
        else:
            system_paths.extend(glob.glob("C:\\Program Files\\Hamlib*\\bin"))
            system_paths.extend(glob.glob("C:\\Program Files (x86)\\Hamlib*\\bin"))

        for path in system_paths:
            potential_path = os.path.join(path, binary_name)
            if os.path.isfile(potential_path):
                binary_paths.append(potential_path)

    return binary_paths



def kill_and_execute(binary_path, additional_args=None):
    """
    Kills any running instances of the binary across Linux, macOS, and Windows, then starts a new one non-blocking.

    :param binary_path: The full path to the binary to execute.
    :param additional_args: A list of additional arguments to pass to the binary.
    :return: subprocess.Popen object of the started process
    """
    # Kill any existing instances of the binary
    for proc in psutil.process_iter(attrs=['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            # Ensure cmdline is iterable and not None
            if cmdline and binary_path in ' '.join(cmdline):
                proc.kill()
                print(f"Killed running instance with PID: {proc.info['pid']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass  # Process no longer exists or no permission to kill

    # Execute the binary with additional arguments non-blocking
    command = [binary_path] + (additional_args if additional_args else [])
    return subprocess.Popen(command)