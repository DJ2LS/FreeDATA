#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import time

sys.path.insert(0,'..')
sys.path.insert(0,'../tnc')
import data_handler
import helpers
import modem
import static

parser = argparse.ArgumentParser(description='ARQ TEST')
parser.add_argument('--ISS', dest="ISS", action="store_true")
parser.add_argument('--IRS', dest="IRS", action="store_true")

parser.add_argument('--CQ', dest="CQ", action="store_true")
parser.add_argument('--PING', dest="PING", action="store_true")
parser.add_argument('--RAW', dest="RAW", action="store_true")

args = parser.parse_args()

ISS = args.ISS
IRS = args.IRS

CQ = args.CQ
PING = args.PING
RAW = args.RAW

# ------ initialize TNC with test mode
data_handler.TESTMODE = True
modem.TESTMODE = True
static.HAMLIB_RADIOCONTROL = 'disabled'

if ISS:
    modem.RXCHANNEL = "hfchannel1"
    modem.TXCHANNEL = "hfchannel2"

    mycallsign = bytes('DJ2LS-2', 'utf-8')
    mycallsign = helpers.callsign_to_bytes(mycallsign)
    static.MYCALLSIGN = helpers.bytes_to_callsign(mycallsign)
    static.MYCALLSIGN_CRC = helpers.get_crc_24(static.MYCALLSIGN)
    static.MYGRID = bytes('AA12aa', 'utf-8')
    static.SSID_LIST = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    # set dx dxcallsign
    dxcallsign = b'DN2LS-0'
    dxcallsign = helpers.callsign_to_bytes(dxcallsign)
    dxcallsign = helpers.bytes_to_callsign(dxcallsign)
    static.DXCALLSIGN = dxcallsign
    static.DXCALLSIGN_CRC = helpers.get_crc_24(static.DXCALLSIGN)

if IRS:
    modem.RXCHANNEL = "hfchannel2"
    modem.TXCHANNEL = "hfchannel1"

    mycallsign = bytes('DN2LS-2', 'utf-8')
    mycallsign = helpers.callsign_to_bytes(mycallsign)
    static.MYCALLSIGN = helpers.bytes_to_callsign(mycallsign)
    static.MYCALLSIGN_CRC = helpers.get_crc_24(static.MYCALLSIGN)
    static.MYGRID = bytes('AA12aa', 'utf-8')
    static.RESPOND_TO_CQ = True
    static.SSID_LIST = [0,1,2,3,4,5,6,7,8,9]

# start data handler
data_handler.DATA()

# start modem
modem = modem.RF()

# transmit RAW File
if RAW:
    bytes_out = b'{"dt":"f","fn":"zeit.txt","ft":"text\\/plain","d":"data:text\\/plain;base64,MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=","crc":"123123123"}'

    # add command to data qeue
    '''
    data[0] == 'ARQ_RAW':
        # [0] ARQ_RAW
        # [1] DATA_OUT bytes
        # [2] MODE int
        # [3] N_FRAMES_PER_BURST int
        # [4] self.transmission_uuid str
        # [5] mycallsign with ssid
    '''
    #data_handler.DATA_QUEUE_TRANSMIT.put(['ARQ_RAW', bytes_out, 255, n_frames_per_burst, '123', b'DJ2LS-0'])

# transmit CQ
if CQ:
    for _ in range(4):
        data_handler.DATA_QUEUE_TRANSMIT.put(['CQ'])

# transmit PING
if PING:
    for _ in range(4):
        data_handler.DATA_QUEUE_TRANSMIT.put(['PING', b'DN2LS-2'])

while 1:
    time.sleep(0.01)
