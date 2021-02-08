#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 21:25:14 2020

@author: DJ2LS
"""

import time
import threading
import logging
import crcengine


import static

    
    
def get_crc_8(data):
    crc_algorithm = crcengine.new('crc8-ccitt') #load crc8 library
    crc_data = crc_algorithm(data)
    crc_data = crc_data.to_bytes(1, byteorder='big') 
    return crc_data

def get_crc_16(data):
    crc_algorithm = crcengine.new('crc16-ccitt-false') #load crc16 library
    crc_data = crc_algorithm(data)
    crc_data = crc_data.to_bytes(2, byteorder='big') 
    return crc_data