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

def watchdog():
    """
    Author: DJ2LS
    
    watchdog master function. Frome here we call the watchdogs
    """
    while True:
        time.sleep(0.01)
        connection_keep_alive_watchdog()
        data_channel_keep_alive_watchdog()
        
def connection_keep_alive_watchdog():
    """
    Author: DJ2LS
    
    Function to trigger a DISCONNECT, if timeout for receiving a keep alive frame is reached
   
    """

    if static.ARQ_STATE == 'CONNECTED' and not static.ARQ_READY_FOR_DATA and static.TNC_STATE == 'IDLE' and static.ARQ_SEND_KEEP_ALIVE:
        time.sleep(0.01)
        if static.ARQ_CONNECTION_KEEP_ALIVE_RECEIVED + 10 > time.time():
            static.ARQ_SEND_KEEP_ALIVE = True
        else:
            # TODO: show time out message
            static.ARQ_SEND_KEEP_ALIVE = False
            static.ARQ_CONNECTION_KEEP_ALIVE_RECEIVED = 0
            static.ARQ_STATE = 'IDLE'
            print("keep alive timeout")
            asyncio.run(data_handler.arq_disconnect())
            
def data_channel_keep_alive_watchdog():
    """
    Author: DJ2LS
    
   
    """

    if static.ARQ_STATE == 'CONNECTED' and static.TNC_STATE == 'BUSY' and not static.ARQ_SEND_KEEP_ALIVE:
        time.sleep(0.01)
        if static.ARQ_DATA_CHANNEL_LAST_RECEIVED + 10 > time.time():
            static.ARQ_SEND_KEEP_ALIVE = False
            #print("alles okay mit den daten....")
        else:
            # TODO: show time out message
            # static.ARQ_SEND_KEEP_ALIVE = True
            static.ARQ_DATA_CHANNEL_LAST_RECEIVED = 0
            print("data keep alive timeout")
            arq_reset_frame_machine()
            data_handler.arq_transmit_keep_alive()
            
                        
    
    
    
async def set_after_timeout():
    """
    Author: DJ2LS
    """
    while True:
        time.sleep(1)
        static.ARQ_RX_ACK_TIMEOUT = True
        await asyncio.sleep(1.1)
    # await asyncio.sleep(timeout)
    #vars()[variable] = value


def arq_disconnect_timeout():
    """
    Author: DJ2LS
    """
    static.ARQ_WAIT_FOR_DISCONNECT = True
    logging.debug("ARQ_WAIT_FOR_DISCONNECT")


def arq_ack_timeout():
    """
    Author: DJ2LS
    """
    if static.CHANNEL_STATE == 'RECEIVING_SIGNALLING':
        static.ARQ_RX_ACK_TIMEOUT = True
        logging.debug("ARQ_RX_ACK_TIMEOUT")


def arq_rpt_timeout():
    """
    Author: DJ2LS
    """
    if static.CHANNEL_STATE == 'RECEIVING_SIGNALLING':
        static.ARQ_RX_RPT_TIMEOUT = True
        logging.debug("ARQ_RX_RPT_TIMEOUT")


def arq_frame_timeout():
    """
    Author: DJ2LS
    """
    if static.CHANNEL_STATE == 'RECEIVING_SIGNALLING':
        static.ARQ_RX_FRAME_TIMEOUT = True
        logging.debug("ARQ_RX_FRAME_TIMEOUT")


def arq_reset_timeout(state):
    """
    Author: DJ2LS
    """
    static.ARQ_RX_ACK_TIMEOUT = state
    static.ARQ_RX_FRAME_TIMEOUT = state
    static.ARQ_RX_RPT_TIMEOUT = state


def arq_reset_ack(state):
    """
    Author: DJ2LS
    """
    static.ARQ_ACK_RECEIVED = state
    static.ARQ_RPT_RECEIVED = state
    static.ARQ_FRAME_ACK_RECEIVED = state


def arq_reset_frame_machine():
    """
    Author: DJ2LS

    Reset the frame machine parameters to default,
    so we need to call just a function

    """
    arq_reset_timeout(False)
    arq_reset_ack(False)
    static.TX_N_RETRIES = 0
    static.ARQ_N_SENT_FRAMES = 0
    static.ARQ_TX_N_FRAMES_PER_BURST = 0
    static.ARQ_TX_N_CURRENT_ARQ_FRAME = 0
    static.ARQ_TX_N_TOTAL_ARQ_FRAMES = 0
    static.ARQ_TX_N_CURRENT_ARQ_FRAME = 0

    static.ARQ_RX_N_CURRENT_ARQ_FRAME = 0
    static.ARQ_N_ARQ_FRAMES_PER_DATA_FRAME = 0
    static.ARQ_FRAME_BOF_RECEIVED = False
    static.ARQ_FRAME_EOF_RECEIVED = False

    static.TNC_STATE = 'IDLE'
    static.ARQ_SEND_KEEP_ALIVE = True
    static.CHANNEL_STATE = 'RECEIVING_SIGNALLING'
    static.ARQ_READY_FOR_DATA = False


def setup_logging():
    """
    Author: DJ2LS

    Set the custom logging format so we can use colors

    """

    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)s:\t%(message)s', datefmt='%H:%M:%S', level=logging.INFO)

    logging.addLevelName(logging.DEBUG, "\033[1;36m%s\033[1;0m" % logging.getLevelName(logging.DEBUG))
    logging.addLevelName(logging.INFO, "\033[1;37m%s\033[1;0m" % logging.getLevelName(logging.INFO))
    logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
    logging.addLevelName(logging.ERROR, "\033[1;31m%s\033[1;0m" % "FAILED")
    #logging.addLevelName( logging.ERROR, "\033[1;31m%s\033[1;0m" % logging.getLevelName(logging.ERROR))
    logging.addLevelName(logging.CRITICAL, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.CRITICAL))

    logging.addLevelName(25, "\033[1;32m%s\033[1;0m" % "SUCCESS")
    logging.addLevelName(24, "\033[1;34m%s\033[1;0m" % "DATA")

    # https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    # 'DEBUG'   : 37, # white
    # 'INFO'    : 36, # cyan
    # 'WARNING' : 33, # yellow
    # 'ERROR'   : 31, # red
    # 'CRITICAL': 41, # white on red bg
