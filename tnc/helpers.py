#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 21:25:14 2020

@author: DJ2LS
"""

import time
import logging
import asyncio
import crcengine
import static
import data_handler


def wait(seconds):
    timeout = time.time() + seconds

    while time.time() < timeout:
        time.sleep(0.01)
    return True
    
    

def get_crc_8(data):
    """
    Author: DJ2LS

    Get the CRC8 of a byte string

    param: data = bytes()
    """
    crc_algorithm = crcengine.new('crc8-ccitt')  # load crc8 library
    crc_data = crc_algorithm(data)
    crc_data = crc_data.to_bytes(1, byteorder='big')
    return crc_data


def get_crc_16(data):
    """
    Author: DJ2LS

    Get the CRC16 of a byte string

    param: data = bytes()
    """
    crc_algorithm = crcengine.new('crc16-ccitt-false')  # load crc16 library
    crc_data = crc_algorithm(data)
    crc_data = crc_data.to_bytes(2, byteorder='big')
    return crc_data




def add_to_heard_stations(dxcallsign, dxgrid, datatype, snr, offset, frequency):
    # check if buffer empty
    if len(static.HEARD_STATIONS) == 0:
        static.HEARD_STATIONS.append([dxcallsign, dxgrid, int(time.time()), datatype, snr, offset, frequency])
    # if not, we search and update
    else:
        for i in range(0, len(static.HEARD_STATIONS)):
            # update callsign with new timestamp
            if static.HEARD_STATIONS[i].count(dxcallsign) > 0:
                static.HEARD_STATIONS[i] = [dxcallsign, dxgrid, int(time.time()), datatype, snr, offset, frequency]
                break
            # insert if nothing found
            if i == len(static.HEARD_STATIONS) - 1:
                static.HEARD_STATIONS.append([dxcallsign, dxgrid, int(time.time()), datatype, snr, offset, frequency])
                break


#    for idx, item in enumerate(static.HEARD_STATIONS):
#        if dxcallsign in item:
#            item = [dxcallsign, int(time.time())]
#            static.HEARD_STATIONS[idx] = item

def setup_logging():
    """
    Author: DJ2LS

    Set the custom logging format so we can use colors

    # https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    # 'DEBUG'   : 37, # white
    # 'INFO'    : 36, # cyan
    # 'WARNING' : 33, # yellow
    # 'ERROR'   : 31, # red
    # 'CRITICAL': 41, # white on red bg

    """

    logging.basicConfig(level=logging.INFO,encoding='utf-8',format='%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s',datefmt='%H:%M:%S',handlers=[logging.FileHandler("FreeDATA-TNC.log"), logging.StreamHandler()])

    logging.addLevelName(logging.DEBUG, "\033[1;36m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))
    logging.addLevelName(logging.INFO, "\033[1;37m%s\033[1;0m" % logging.getLevelName(logging.INFO))
    logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
    logging.addLevelName(logging.ERROR, "\033[1;31m%s\033[1;0m" % "FAILED")
    #logging.addLevelName( logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
    logging.addLevelName(logging.CRITICAL, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.CRITICAL))

    logging.addLevelName(25, "\033[1;32m%s\033[1;0m" % "SUCCESS")
    logging.addLevelName(24, "\033[1;34m%s\033[1;0m" % "DATA")
