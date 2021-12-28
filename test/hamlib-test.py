#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import ctypes
from ctypes import *
import pathlib

from enum import Enum


class DEBUGLEVEL(Enum):
    RIG_DEBUG_NONE = 0
    RIG_DEBUG_BUG = 1
    RIG_DEBUG_ERR = 2
    RIG_DEBUG_WARN = 3
    RIG_DEBUG_VERBOSE = 4
    RIG_DEBUG_TRACE = 5
    RIG_DEBUG_CACHE = 6

class RETCODE(Enum):
    RIG_OK = 0
    RIG_EINVAL = 1
    RIG_ECONF = 2
    RIG_ENOMEM = 3
    RIG_ENIMPL = 4	
    RIG_ETIMEOUT = 5	
    RIG_EIO = 6
    RIG_EINTERNAL = 7 	
    RIG_EPROTO = 8
    RIG_ERJCTED = 9
    RIG_ETRUNC = 10
    RIG_ENAVAIL = 11
    RIG_ENTARGET = 12
    RIG_BUSERROR = 13
    RIG_BUSBUSY = 14
    RIG_EARG = 15
    RIG_EVFO = 16
    RIG_EDOM = 17















libname = pathlib.Path("../tnc/lib/hamlib/linux/libhamlib.so")
hamlib = ctypes.CDLL(libname)


class SERIAL(ctypes.Structure):
    _fields_ = [
        ("data_bits", ctypes.c_int),
        ("stop_bits", ctypes.c_int),
        ("rate", ctypes.c_int),
    ]
    
class PARM(ctypes.Structure):
    _fields_ = [
        ("serial", SERIAL),
    ]
    
class RIGPORT(ctypes.Structure):
    _fields_ = [
        ("pathname", ctypes.c_float),
        ("parm", PARM),
    ]
    
class STATE(ctypes.Structure):
    _fields_ = [
        ("rigport", RIGPORT),


    ]

class MY_RIG(ctypes.Structure):
    _fields_ = [
        #("Nc", ctypes.c_int),
        #("snr_est", ctypes.c_float),
        #("rx_symbols", (ctypes.c_float * MODEM_STATS_NR_MAX)*MODEM_STATS_NC_MAX),
        #("nr", ctypes.c_int),
        #("sync", ctypes.c_int),
        #("foff", ctypes.c_float),
        #("rx_timing", ctypes.c_float),
        #("clock_offset", ctypes.c_float),
        #("sync_metric", ctypes.c_float),
        ("pathname", ctypes.c_uchar),
        ("state", STATE),

    ]
    
    
'''    
        myport.type.rig = RIG_PORT_SERIAL;
        myport.parm.serial.rate = 9600;
        myport.parm.serial.data_bits = 8;
        myport.parm.serial.stop_bits = 1;
        myport.parm.serial.parity = RIG_PARITY_NONE;
        myport.parm.serial.handshake = RIG_HANDSHAKE_NONE;
        strncpy(myport.pathname, SERIAL_PORT, HAMLIB_FILPATHLEN - 1);''
'''        


hamlib.rig_set_debug(6) #6

model = 3085 #3085 = ICOM 6 = DUMMY
my_rig = MY_RIG()
my_rig.state.rigport.parm.serial.data_bits = 7

#rig = hamlib.rig_init(my_rig)

#hamlib.serial_setup()
#hamlib.serial_open('dev12')

retcode = hamlib.rig_open(my_rig)



hamlib.rig_close(rig)














#riginfo = create_string_buffer(1024)
#retcode = hamlib.rig_get_rig_info(rig, riginfo, 1024);

'''
char riginfo[1024];
retcode = rig_get_rig_info(rig, riginfo, sizeof(riginfo));
'''
