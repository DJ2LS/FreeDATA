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


bytes_out = b'{"dt":"f","fn":"zeit.txt","ft":"text\\/plain","d":"data:text\\/plain;base64,MyBtb2Rlcywgb2huZSBjbGFzcwowLjAwMDk2OTQ4MTE4MDk5MTg0MTcKCjIgbW9kZXMsIG9obmUgY2xhc3MKMC4wMDA5NjY1NDUxODkxMjI1Mzk0CgoxIG1vZGUsIG9obmUgY2xhc3MKMC4wMDA5NjY5NzY1NTU4Nzc4MjA5Cg==","crc":"123123123"}'

mode = 12
n_frames_per_burst = 1

data_handler.TESTMODE = True
data_handler.open_dc_and_transmit(bytes_out, mode, n_frames_per_burst)

