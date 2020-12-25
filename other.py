#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 25 21:25:14 2020

@author: DJ2LS
"""

import time
import threading

import static



def timeout():
    print("TIMEOUT REACHED!")
    #static.ACK_TIMEOUT = seconds
    #time.sleep(seconds)    
    static.ACK_TIMEOUT = 1