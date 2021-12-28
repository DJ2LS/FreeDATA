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
        ("parity", ctypes.c_int),
        ("handshake", ctypes.c_void_p),
    ]
    
class PARM(ctypes.Structure):
    _fields_ = [
        ("serial", SERIAL),
    ]
    
class TYPE(ctypes.Structure):
    _fields_ = [
        ("rig", ctypes.c_void_p),
    ]
    
class MYPORT(ctypes.Structure):
    _fields_ = [
        ("pathname", ctypes.c_char),
        ("model", ctypes.c_int),
        ("parm", PARM),
        ("type", TYPE),

    ]


hamlib.rig_set_debug(9) #6
myrig_model = 3085 #3085 = ICOM 6 = DUMMY

myport = MYPORT()
myport.parm.serial.data_bits = 7
myport.parm.serial.stop_bits = 2
myport.parm.serial.rate = 9600



rig = hamlib.rig_init(myrig_model)

retcode = hamlib.rig_set_parm(rig, 'stop_bits', 5)
print(retcode)

'''
parameter = create_string_buffer(16)
retcode = hamlib.rig_get_parm(rig, 0, parameter)
print(retcode)
print(bytes(parameter))
'''


# attempt to access global vars. Maybe we can access structures as well?
# https://github.com/Hamlib/Hamlib/blob/f5b229f9dc4b4364d2f40e0b0b415e92c9a371ce/src/rig.c#L95
hamlib_version = ctypes.cast(hamlib.hamlib_version, ctypes.POINTER(ctypes.c_char*21))
print(hamlib_version.contents.value)


'''
retcode = hamlib.rig_has_get_parm(rig, 7)
print(retcode)
'''

'''
retcode = hamlib.rig_open(rig)
print(retcode)


hamlib.rig_close(rig)
'''



#riginfo = create_string_buffer(1024)
#retcode = hamlib.rig_get_rig_info(rig, riginfo, 1024);

'''
char riginfo[1024];
retcode = rig_get_rig_info(rig, riginfo, sizeof(riginfo));
'''
