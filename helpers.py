#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 21:25:14 2020

@author: DJ2LS
"""

import time
import threading
import logging
from colorlog import ColoredFormatter
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
       
def arq_ack_timeout():
    if static.ARQ_STATE == 'RECEIVING_SIGNALLING':
        static.ARQ_RX_ACK_TIMEOUT = True
        logging.debug("ARQ_RX_ACK_TIMEOUT")
    
def arq_rpt_timeout():
    if static.ARQ_STATE == 'RECEIVING_SIGNALLING':
        static.ARQ_RX_RPT_TIMEOUT = True    
        logging.debug("ARQ_RX_RPT_TIMEOUT")    

def arq_frame_timeout():
    if static.ARQ_STATE == 'RECEIVING_SIGNALLING':
        static.ARQ_RX_FRAME_TIMEOUT = True    
        logging.debug("ARQ_RX_FRAME_TIMEOUT")     
                
def arq_reset_timeout(state):
    static.ARQ_RX_ACK_TIMEOUT = state
    static.ARQ_RX_FRAME_TIMEOUT = state
    static.ARQ_RX_RPT_TIMEOUT = state
    
def arq_reset_ack(state):  
    static.ARQ_ACK_RECEIVED = state
    static.ARQ_RPT_RECEIVED = state
    static.ARQ_FRAME_ACK_RECEIVED = state
    
def arq_reset_frame_machine():
    arq_reset_timeout(False)
    arq_reset_ack(False)
    static.TX_N_RETRIES = 0
    static.ARQ_N_SENT_FRAMES = 0
    static.ARQ_TX_N_FRAMES_PER_BURST = 0
    

