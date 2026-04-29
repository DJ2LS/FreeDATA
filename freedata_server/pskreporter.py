# -*- coding: UTF-8 -*-
"""
PSKReporter uploader for FreeDATA
Author: Kai Gunter Brandt (LA3QMA)
"""

import time
import struct
import socket
import sys
import json
from datetime import datetime
from typing import Dict, Any, Tuple, List, Iterable, Union
from pathlib import Path
import structlog

log = structlog.get_logger("pskreporter")

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
SEQ_PATH = Path("PSKReporter_seq.txt")
DEFAULT_SEQ = 1
SESSION_ID = int(time.time())

HOST = "report.pskreporter.info"
PORT_TEST = 14739
PORT_LIVE = 4739

# Global station metadata used for receiver record
_mycall = ""
_mygrid = ""
_mysw = ""


# ----------------------------------------------------------------------
# sequence number handling
# ----------------------------------------------------------------------
def load_seq() -> int:
    if not SEQ_PATH.is_file():
        return DEFAULT_SEQ
    try:
        return int(SEQ_PATH.read_text().strip())
    except:
        return DEFAULT_SEQ


def save_seq(seq: int) -> None:
    try:
        SEQ_PATH.write_text(str(seq))
    except Exception as e:
        sys.stderr.write(f"Could not increase sequence: {e}\n")


# ----------------------------------------------------------------------
# packing functions
# ----------------------------------------------------------------------
def hx(a):
    return bytes(a)


def pstr(s: str) -> bytes:
    b = s.encode("utf-8")
    if len(b) > 255:
        raise ValueError("String too long for pstr()")
    return bytes([len(b)]) + b


def p16(i: int) -> bytes:
    return struct.pack(">H", i)


def p32(i: int) -> bytes:
    return struct.pack(">I", i)


def pad(b: bytes) -> bytes:
    while len(b) % 4 != 0:
        b += b"\x00"
    return b


# ----------------------------------------------------------------------
# Beacon constructor
# ----------------------------------------------------------------------
def make_psk_beacon(callsign, grid, frequency, snr, timestamp=None) -> Dict[str, Any]:
    return {
        "callsign": callsign,
        "gridsquare": grid,
        "frequency": int(float(frequency)),
        "snr": int(float(snr)),
        "timestamp": timestamp or int(time.time())
    }


# ----------------------------------------------------------------------
# Transform beacon
# ----------------------------------------------------------------------
def transform_beacon_to_spot(beacon: Dict[str, Any]) -> Tuple:
    """
    Convert FreeDATA beacon into a 7-field PSKReporter:
    (call, freq_hz, imd, snr, mode, grid, epoch)
    """
    call = beacon["callsign"].split("-")[0]
    grid_check = beacon.get("gridsquare", "")
    grid = grid_check[:-2] + grid_check[-2:].lower()
    log.warning("Raw grid: ", raw_grid=grid)
    freq_hz = int(float(beacon["frequency"]))
    imd = 0
    snr = int(beacon["snr"])
    mode = "FreeDATA"

    ts = beacon.get("timestamp")
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            epoch = int(dt.timestamp())
        except:
            epoch = int(time.time())
    else:
        epoch = int(ts)

    if not (-128 <= snr <= 127):
        raise ValueError(f"SNR {snr} out of range")

    return (call, freq_hz, snr, imd, mode, grid, epoch)


# ----------------------------------------------------------------------
# Validate the spot structure
# ----------------------------------------------------------------------
def validate_spot(spot: Union[List, Tuple]) -> Tuple:
    call, freq_hz, snr, imd, mode, grid, epoch = spot

    return (
        str(call),
        int(freq_hz),
        int(snr),
        int(imd),
        str(mode),
        str(grid),
        int(epoch)
    )


# ----------------------------------------------------------------------
# Packet builder
# ----------------------------------------------------------------------
def build_packet(senders: List[Tuple]) -> bytes:
    global _mycall, _mygrid, _mysw

    # Receiver format descriptor
    rrf = hx([
        0x00, 0x03, 0x00, 0x24, 0x99, 0x92, 0x00, 0x03, 0x00, 0x00,
        0x80, 0x02, 0xFF, 0xFF, 0x00, 0x00, 0x76, 0x8F,
        0x80, 0x04, 0xFF, 0xFF, 0x00, 0x00, 0x76, 0x8F,
        0x80, 0x08, 0xFF, 0xFF, 0x00, 0x00, 0x76, 0x8F,
        0x00, 0x00
    ])

    # Sender format descriptor
    srf = hx([
        0x00, 0x02, 0x00, 0x44, 0x99, 0x93, 0x00, 0x08,
        0x80, 0x01, 0xFF, 0xFF, 0x00, 0x00, 0x76, 0x8F,
        0x80, 0x05, 0x00, 0x04, 0x00, 0x00, 0x76, 0x8F,
        0x80, 0x06, 0x00, 0x01, 0x00, 0x00, 0x76, 0x8F,
        0x80, 0x07, 0x00, 0x01, 0x00, 0x00, 0x76, 0x8F,
        0x80, 0x0A, 0xFF, 0xFF, 0x00, 0x00, 0x76, 0x8F,
        0x80, 0x0B, 0x00, 0x01, 0x00, 0x00, 0x76, 0x8F,
        0x80, 0x03, 0xFF, 0xFF, 0x00, 0x00, 0x76, 0x8F,
        0x00, 0x96, 0x00, 0x04
    ])

    # Receiver record
    rr = pad(pstr(_mycall) + pstr(_mygrid) + pstr(_mysw))
    rr = hx([0x99, 0x92]) + p16(len(rr) + 4) + rr

    # Sender records
    sr = b""
    for call, freq_hz, imd, snr, mode, grid, epoch in senders:
        sr += pstr(call)
        sr += p32(freq_hz)
        sr += struct.pack("b", imd)
        sr += struct.pack("b", snr)
        sr += pstr(mode)
        sr += b"\x01"
        sr += pstr(grid)
        sr += p32(epoch)

    sr = pad(sr)
    sr = hx([0x99, 0x93]) + p16(len(sr) + 4) + sr

    seq = load_seq()
    save_seq(seq + 1)

    # Packet header
    header = b""
    header += hx([0x00, 0x0A])
    header += p16(len(rrf) + len(srf) + len(rr) + len(sr) + 16)
    header += p32(int(time.time()))
    header += p32(seq)
    header += p32(SESSION_ID)

    return header + rrf + srf + rr + sr


# ----------------------------------------------------------------------
# UDP Handling
# ----------------------------------------------------------------------
def init_socket(mycall: str, mygrid: str, mysw: str, testing=False) -> socket.socket:
    global _mycall, _mygrid, _mysw
    _mycall = mycall
    _mygrid = mygrid
    _mysw = mysw

    port = PORT_TEST if testing else PORT_LIVE
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((HOST, port))
    return s


def send_bulk(sock: socket.socket, spots: Iterable[Tuple]) -> None:
    validated = []

    for s in spots:
        try:
            validated.append(validate_spot(s))
        except Exception as e:
            log.warning("Invalid spot skipped", error=str(e))

    if not validated:
        raise ValueError("No valid spots")

    pkt = build_packet(validated)
    sock.send(pkt)
    log.info(pkt)
    log.info("PSK packet sent", spots=len(validated))
    log.info(dump_packet(pkt))

def dump_packet(pkt: bytes):
    print(" ".join(f"{b:02x}" for b in pkt))


# ----------------------------------------------------------------------
# Class wrapper used by FreeDATA
# ----------------------------------------------------------------------
class Pskreporter:
    def __init__(self, ctx):
        self.ctx = ctx
        self.modem_version = self.ctx.constants.MODEM_VERSION

    def push(self):
        mycall = f"{self.ctx.config_manager.config['STATION']['mycall']}"
        mygrid = self.ctx.config_manager.config["STATION"]["mygrid"]
        pskreporter_fallback_frequency = self.ctx.config_manager.config["STATION"]["pskreporter_fallback_frequency"]
        version = "FreeDATA " + str(self.modem_version)
        # psk_debug = self.ctx.config_manager.config["STATION"]["pskreporter_debug"]
        # log.info(psk_debug)
        udp = init_socket(mycall, mygrid, version, testing=False)

        spots = []

        for heard in self.ctx.state_manager.heard_stations:
            try:
                callsign = heard[0]
                grid_check = heard[1]
                grid = grid_check[:-2] + grid_check[-2:].lower()
                timestamp = heard[2]
                freq = pskreporter_fallback_frequency if heard[6] == "---" else heard[6]
                snr = heard[4].split("/")[1] if isinstance(heard[4], str) and "/" in heard[4] else heard[4]
                beacon = make_psk_beacon(callsign, grid, freq, snr, timestamp)
                spots.append(transform_beacon_to_spot(beacon))

            except Exception as e:
                log.warning("Skipping bad heard record", error=str(e))

        if spots:
            send_bulk(udp, spots)
            log.info(spots)
            log.info(grid)
            log.info(snr)
            log.info(freq)
        else:
            log.info("No PSKReporter spots to send")
