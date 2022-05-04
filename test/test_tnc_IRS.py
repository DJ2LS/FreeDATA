#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 23 07:04:24 2020

@author: DJ2LS
"""

import sys
sys.path.insert(0,'..')
sys.path.insert(0,'../tnc')
import data_handler
import argparse
import codec2
import modem
import static
import time
import helpers

parser = argparse.ArgumentParser(description='ARQ TEST')
parser.add_argument('--mode', dest="FREEDV_MODE", type=str, choices=['datac0', 'datac1', 'datac3'], default='datac0')
parser.add_argument('--framesperburst', dest="N_FRAMES_PER_BURST", default=1, type=int)
args = parser.parse_args()


# enable testmode
data_handler.TESTMODE = True
modem.TESTMODE = True
modem.RXCHANNEL = "hfchannel2"
modem.TXCHANNEL = "hfchannel1"
static.HAMLIB_RADIOCONTROL = 'disabled'

mycallsign = bytes('DN2LS-2', 'utf-8')
mycallsign = helpers.callsign_to_bytes(mycallsign)
static.MYCALLSIGN = helpers.bytes_to_callsign(mycallsign)
static.MYCALLSIGN_CRC = helpers.get_crc_24(static.MYCALLSIGN) 
static.MYGRID = bytes('AA12aa', 'utf-8')
static.SSID_LIST = [0,1,2,3,4,5,6,7,8,9]
static.HAMLIB_RADIOCONTROL = 'disabled'
static.RESPOND_TO_CQ = True

# start data handler
data_handler.DATA()
    
# start modem
modem = modem.RF()
      
while 1:
    time.sleep(0.01)
