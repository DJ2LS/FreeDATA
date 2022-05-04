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
modem.RXCHANNEL = "hfchannel1"
modem.TXCHANNEL = "hfchannel2"
static.HAMLIB_RADIOCONTROL = 'disabled'
mycallsign = bytes('DJ2LS-2', 'utf-8')
mycallsign = helpers.callsign_to_bytes(mycallsign)
static.MYCALLSIGN = helpers.bytes_to_callsign(mycallsign)
static.MYCALLSIGN_CRC = helpers.get_crc_24(static.MYCALLSIGN) 
static.MYGRID = bytes('AA12aa', 'utf-8')
static.SSID_LIST = [0,1,2,3,4,5,6,7,8,9]

dxcallsign = b'DN2LS-0'
dxcallsign = helpers.callsign_to_bytes(dxcallsign)
dxcallsign = helpers.bytes_to_callsign(dxcallsign)
static.DXCALLSIGN = dxcallsign
static.DXCALLSIGN_CRC = helpers.get_crc_24(static.DXCALLSIGN)
                    
                    

bytes_out = b'{"dt":"f","fn":"zeit.txt","ft":"text\\/plain","d":"data:text\\/plain;base64,MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5CgMyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg=","crc":"123123123"}'

# start data handler
data_handler.DATA()
    
# start modem
modem = modem.RF()
      
mode = codec2.freedv_get_mode_value_by_name(args.FREEDV_MODE)
n_frames_per_burst = args.N_FRAMES_PER_BURST


# add command to data qeue
'''        
elif data[0] == 'ARQ_RAW':
    # [0] ARQ_RAW
    # [1] DATA_OUT bytes
    # [2] MODE int
    # [3] N_FRAMES_PER_BURST int
    # [4] self.transmission_uuid str
    # [5] mycallsign with ssid
'''
#data_handler.DATA_QUEUE_TRANSMIT.put(['ARQ_RAW', bytes_out, 255, n_frames_per_burst, '123', b'DJ2LS-0'])
for i in range(0,4):
    data_handler.DATA_QUEUE_TRANSMIT.put(['CQ'])
 
#for i in range(0,4):    
#    data_handler.DATA_QUEUE_TRANSMIT.put(['PING', b'DN2LS-2'])

while 1:
    time.sleep(0.01)
